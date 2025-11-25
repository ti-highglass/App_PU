"""Ferramenta para envio de comandos ZPL para impressoras instaladas no Windows.

Funcionalidades principais:
- CLI tradicional para envio de texto/comandos, com suporte a templates .prn.
- Substituição de um ou múltiplos marcadores dentro do template (via `--token` e
  `--var TOKEN=valor`).
- Servidor HTTP simples (Flask) que expõe um endpoint POST /print para receber jobs remotos.

O formato JSON esperado pelo endpoint é:
{
    "text": "conteúdo a ser impresso" (necessário quando não houver template),
    "printer": "Nome da impressora" (opcional, usa padrão se omitido),
    "model_prn": "arquivo.prn" (opcional, relativo ao diretório base do script),
    "token": "{{1}}" (opcional, marcador principal),
    "variables": {"{{2}}": "valor", "3": "valor"} (opcional, marcadores adicionais)
}
"""
from __future__ import annotations

import argparse
import json
import locale
import os
import subprocess
import sys
import tempfile
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from flask import Flask, Response

# Payload de teste utilizado pela flag --zpl-test
ZPL_TEST_PAYLOAD = """^XA
^LH0,0
^FO40,40
^A0N,36,36
^FDTeste^FS
^XZ
"""

BASE_DIR = Path(__file__).resolve().parent
_PRINT_LOCK = threading.Lock()

DEFAULT_ENCODING = locale.getpreferredencoding(False)
if not DEFAULT_ENCODING or DEFAULT_ENCODING.lower() in {"ansi_x3.4-1968", "us-ascii"}:
    DEFAULT_ENCODING = "utf-8"


class PrintJobError(RuntimeError):
    """Erro ao montar ou enviar o job para a impressora."""


@dataclass
class PrintJob:
    text: str
    printer: Optional[str] = None
    template: Optional[Path] = None
    token: str = "{{1}}"
    encoding: str = DEFAULT_ENCODING
    variables: Optional[dict[str, str]] = None


def _read_text(args: argparse.Namespace) -> str:
    if args.zpl_test:
        return ZPL_TEST_PAYLOAD

    if args.text:
        return args.text

    if args.stdin or not sys.stdin.isatty():
        return sys.stdin.read()

    print("Digite o texto (ou comandos) a ser impresso. Encerre com uma linha vazia.")
    lines = []
    try:
        while True:
            line = input()
            if line == "":
                break
            lines.append(line)
    except EOFError:
        pass

    return "\n".join(lines)


def _detect_default_printer() -> str:
    try:
        import win32print  # type: ignore
    except Exception:
        ps_query = (
            "Get-CimInstance -ClassName Win32_Printer | "
            "Where-Object { $_.Default -eq $true } | "
            "Select-Object -First 1 -ExpandProperty Name"
        )
        try:
            completed = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_query],
                capture_output=True,
                text=True,
                check=True,
            )
        except subprocess.CalledProcessError as exc:
            raise PrintJobError("Não foi possível consultar a impressora padrão pelo PowerShell.") from exc

        printer = completed.stdout.strip()
        if printer:
            return printer
        raise PrintJobError("Nenhuma impressora padrão encontrada pelo PowerShell.")

    import win32print  # type: ignore  # pragma: no cover - import já validado acima

    printer = win32print.GetDefaultPrinter()
    if printer:
        return printer
    raise PrintJobError("Nenhuma impressora padrão encontrada pelo Windows.")


def _resolve_template(template_value: str) -> Path:
    candidate = Path(template_value)
    if not candidate.is_absolute():
        candidate = (BASE_DIR / candidate).resolve()

    if not candidate.exists():
        raise PrintJobError(f"Template não encontrado: {candidate}")

    if not candidate.is_file():
        raise PrintJobError(f"Template inválido (não é arquivo regular): {candidate}")

    try:
        candidate.relative_to(BASE_DIR)
    except ValueError:
        raise PrintJobError("Templates precisam estar dentro do diretório base do serviço.")

    return candidate


def _token_candidates(token: str) -> list[str]:
    candidates = [token]

    if token.startswith("{{") and token.endswith("}}") and len(token) > 4:
        inner = token[2:-2]
        candidates.append(f"{{{inner}}}")
        candidates.append(inner)
    elif token.startswith("{") and token.endswith("}") and len(token) > 2:
        inner = token[1:-1]
        candidates.append(f"{{{{{inner}}}}}")
        candidates.append(inner)
    else:
        candidates.append(f"{{{token}}}")
        candidates.append(f"{{{{{token}}}}}")

    # Remove duplicados preservando a ordem de descoberta.
    return list(dict.fromkeys(candidates))


def _normalize_token_key(token: str) -> str:
    if token.startswith("{{") and token.endswith("}}") and len(token) > 4:
        return token[2:-2]
    if token.startswith("{") and token.endswith("}") and len(token) > 2:
        return token[1:-1]
    return token


def _apply_template(
    template_path: Path,
    payload: Optional[str],
    token: str,
    extra_variables: Optional[dict[str, str]] = None,
) -> str:
    template_text = template_path.read_text(encoding="utf-8-sig")

    replacements: list[tuple[str, str]] = []
    if payload is not None:
        replacements.append((token, payload))

    if extra_variables:
        for raw_token, value in extra_variables.items():
            replacements.append((raw_token, value))

    successful_tokens: set[str] = set()

    for raw_token, value in replacements:
        for candidate in _token_candidates(raw_token):
            if candidate in template_text:
                template_text = template_text.replace(candidate, value)
                successful_tokens.add(_normalize_token_key(raw_token))
                break
    missing_tokens: list[str] = []
    for raw_token, _ in replacements:
        if _normalize_token_key(raw_token) not in successful_tokens:
            missing_tokens.append(raw_token)

    if missing_tokens:
        formatted = ", ".join(f"'{tok}'" for tok in missing_tokens)
        raise PrintJobError(f"Token(s) {formatted} não encontrado(s) em {template_path}.")

    return template_text


def _send_with_win32(job: PrintJob) -> str:
    try:
        import win32print  # type: ignore
    except ImportError as exc:  # pragma: no cover - fallback acionado
        raise PrintJobError("Pacote pywin32 não disponível") from exc

    printer_name = job.printer or win32print.GetDefaultPrinter()
    if not printer_name:
        raise PrintJobError("Nenhuma impressora padrão encontrada")

    try:
        payload = job.text.encode(job.encoding)
    except UnicodeEncodeError as exc:
        raise PrintJobError(
            "Caracteres não suportados pela codificação atual. Defina --encoding ou 'encoding' no JSON."
        ) from exc

    with _PRINT_LOCK:
        handle = win32print.OpenPrinter(printer_name)
        try:
            doc_info = ("Python RAW", None, "RAW")
            win32print.StartDocPrinter(handle, 1, doc_info)
            try:
                written = win32print.WritePrinter(handle, payload)
                if written != len(payload):
                    raise PrintJobError(
                        f"Somente {written} de {len(payload)} bytes enviados à spooler."
                    )
            finally:
                win32print.EndDocPrinter(handle)
        finally:
            win32print.ClosePrinter(handle)

    return printer_name


def _send_with_startfile(job: PrintJob) -> str:
    if os.name != "nt":
        raise PrintJobError("Fallback disponível apenas no Windows")

    target_printer = job.printer or _detect_default_printer()

    try:
        with tempfile.NamedTemporaryFile(
            "w", encoding=job.encoding, suffix=".txt", delete=False
        ) as tmp:
            tmp.write(job.text)
            temp_path = Path(tmp.name)
    except UnicodeEncodeError as exc:
        raise PrintJobError(
            "Caracteres não suportados pela codificação atual. Ajuste o parâmetro de encoding."
        ) from exc

    escaped_path = str(temp_path).replace("'", "''")
    ps_parts = [f"$tmp = '{escaped_path}'", "$verb = 'Print'"]
    start_cmd = "$process = Start-Process -FilePath $tmp -Verb $verb -PassThru"

    if job.printer:
        escaped_printer = target_printer.replace("'", "''")
        ps_parts.append("$verb = 'PrintTo'")
        start_cmd += f" -ArgumentList @('{escaped_printer}')"

    ps_parts.append(start_cmd)
    ps_parts.append("if ($process) { $process.WaitForExit() }")
    ps_script = "; ".join(ps_parts)

    try:
        subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_script],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    finally:
        try:
            temp_path.unlink()
        except OSError:
            pass

    return target_printer


def process_print_job(job: PrintJob) -> str:
    printer_used = _send_with_win32(job)
    return printer_used


def _parse_cli_variables(var_args: Optional[list[str]]) -> Optional[dict[str, str]]:
    if not var_args:
        return None

    variables: dict[str, str] = {}
    for item in var_args:
        if "=" not in item:
            raise PrintJobError("Parâmetros --var devem seguir o formato TOKEN=valor.")
        key, value = item.split("=", 1)
        key = key.strip()
        if not key:
            raise PrintJobError("Tokens informados em --var não podem ser vazios.")
        variables[key] = value

    return variables or None


def _variables_cover_token(token: str, variables: Optional[dict[str, str]]) -> bool:
    if not variables:
        return False

    wanted = {_normalize_token_key(candidate) for candidate in _token_candidates(token)}
    for raw_token in variables.keys():
        if _normalize_token_key(raw_token) in wanted:
            return True
    return False


def _prepare_job_from_args(args: argparse.Namespace) -> PrintJob:
    variables = _parse_cli_variables(args.var)
    token_covered = _variables_cover_token(args.token, variables)

    skip_text_prompt = (
        args.template
        and variables
        and token_covered
        and not args.text
        and not args.stdin
        and not args.zpl_test
        and sys.stdin.isatty()
    )

    text_input: Optional[str] = None
    if not skip_text_prompt:
        text_input = _read_text(args)
        text_is_blank = not text_input.strip()
        if text_is_blank and not variables:
            raise PrintJobError("Nada foi informado para impressão.")
        if text_is_blank and args.template and not token_covered:
            raise PrintJobError(
                "Informe um valor para o marcador principal (texto ou --var)."
            )

    template_path = None
    final_text: str

    if args.template:
        template_path = _resolve_template(str(args.template))
        final_text = _apply_template(template_path, text_input, args.token, variables)
    else:
        if text_input is None:
            raise PrintJobError("Nada foi informado para impressão.")
        final_text = text_input

    return PrintJob(
        text=final_text,
        printer=args.printer,
        encoding=args.encoding,
        template=template_path,
        token=args.token,
        variables=variables,
    )


def run_cli(args: argparse.Namespace) -> int:
    try:
        job = _prepare_job_from_args(args)
        printer = process_print_job(job)
        print(f"Envio direto para a spooler concluído. Impressora: {printer}.")
        return 0
    except PrintJobError as exc:
        print(f"Falha ao imprimir: {exc}", file=sys.stderr)
        return 2


def create_app() -> "Flask":
    try:
        from flask import Flask, jsonify, request
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "Flask não está instalado. Execute 'pip install flask'."
        ) from exc

    app = Flask(__name__)

    @app.route("/health", methods=["GET"])
    def health() -> "Response":
        return jsonify({"status": "ok"})

    @app.route("/print", methods=["POST"])
    def print_endpoint() -> "Response":
        try:
            payload = request.get_json(force=True)
        except Exception as exc:  # pragma: no cover
            return _json_error("JSON inválido", 400, exc)

        if not isinstance(payload, dict):
            return _json_error("Payload deve ser um objeto JSON", 400)

        printer = payload.get("printer")
        if printer is not None and not isinstance(printer, str):
            return _json_error("Campo 'printer' deve ser string quando informado", 400)

        template_arg = payload.get("model_prn")
        token = payload.get("token", "{{1}}")
        encoding = payload.get("encoding", DEFAULT_ENCODING)
        variables_payload = payload.get("variables")

        variables: Optional[dict[str, str]] = None
        if variables_payload is not None:
            if not isinstance(variables_payload, dict):
                return _json_error("Campo 'variables' deve ser um objeto com pares token:valor.", 400)
            variables = {}
            for raw_token, value in variables_payload.items():
                if not isinstance(value, str):
                    return _json_error(
                        "Valores em 'variables' devem ser strings.",
                        400,
                    )
                token_key = str(raw_token).strip()
                if not token_key:
                    return _json_error(
                        "Tokens informados em 'variables' não podem ser vazios.",
                        400,
                    )
                variables[token_key] = value

        text = payload.get("text")
        if text is not None and not isinstance(text, str):
            return _json_error("Campo 'text' deve ser string quando informado.", 400)

        token_covered = _variables_cover_token(token, variables)

        if not template_arg:
            if text is None or not text.strip():
                return _json_error("Campo 'text' é obrigatório quando não há template.", 400)
        else:
            if (text is None or not text.strip()) and not token_covered:
                return _json_error(
                    "Informe um valor para o marcador principal (text ou variables).",
                    400,
                )

        try:
            template_path = None
            text_to_print = text
            if template_arg:
                template_path = _resolve_template(str(template_arg))
                text_to_print = _apply_template(
                    template_path,
                    text_to_print,
                    token,
                    variables,
                )
                if text_to_print is None:
                    return _json_error(
                        "Falha ao processar o template: resultado vazio.",
                        500,
                    )

            job = PrintJob(
                text=text_to_print,
                printer=printer,
                template=template_path,
                token=token,
                encoding=encoding,
                variables=variables,
            )

            printer_used = process_print_job(job)
        except PrintJobError as exc:
            return _json_error(str(exc), 400)
        except Exception as exc:  # pragma: no cover
            return _json_error("Erro interno ao processar impressão", 500, exc)

        return jsonify({
            "status": "ok",
            "printer": printer_used,
        })

    return app


def _json_error(message: str, status: int, exc: Optional[Exception] = None) -> "Response":
    from flask import jsonify

    body = {"status": "error", "message": message}
    if exc is not None:
        body["details"] = str(exc)
    response = jsonify(body)
    response.status_code = status
    return response


def run_server(host: str, port: int, debug: bool) -> None:
    app = create_app()
    app.run(host=host, port=port, debug=debug)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Envia texto puro ou comandos ZPL para a impressora padrão, via CLI ou servidor HTTP.",
    )

    parser.add_argument("--text", help="Texto/comandos a enviar diretamente, substitui o prompt.")
    parser.add_argument(
        "--stdin",
        action="store_true",
        help="Força a leitura integral do texto a partir do stdin.",
    )
    parser.add_argument(
        "--printer",
        help="Nome exato da impressora. Se omitido, usa a impressora padrão.",
    )
    parser.add_argument(
        "--encoding",
        default=DEFAULT_ENCODING,
        help=(
            "Codificação usada ao enviar o texto (padrão detectado no sistema "
            "ou UTF-8 quando o sistema reporta ASCII)."
        ),
    )
    parser.add_argument(
        "--zpl-test",
        action="store_true",
        help="Ignora outras entradas e envia um comando ZPL de teste (^XA...^XZ).",
    )
    parser.add_argument(
        "--template",
        type=Path,
        help="Arquivo .prn com token substituível (padrão {{1}}).",
    )
    parser.add_argument(
        "--var",
        action="append",
        metavar="TOKEN=VALOR",
        help="Marcadores adicionais para templates: ex. --var {{2}}=ABC --var 3=DEF.",
    )
    parser.add_argument(
        "--token",
        default="{{1}}",
        help="Marcador no template a ser substituído pelo texto digitado (padrão {{1}}).",
    )
    parser.add_argument(
        "--serve",
        action="store_true",
        help="Inicia um servidor HTTP (Flask) no host/porta informados.",
    )
    parser.add_argument("--host", default="0.0.0.0", help="Host para o modo servidor (0.0.0.0 expõe na rede).")
    parser.add_argument("--port", type=int, default=5000, help="Porta para o modo servidor.")
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Modo debug do Flask (apenas para desenvolvimento).",
    )

    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    if args.serve:
        if args.text or args.zpl_test or args.template:
            print("Modo servidor não aceita parâmetros de impressão imediata.", file=sys.stderr)
            return 2
        run_server(args.host, args.port, args.debug)
        return 0

    return run_cli(args)


if __name__ == "__main__":
    raise SystemExit(main())
