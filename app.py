from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, send_file, make_response
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta
import pytz
import psycopg2
import psycopg2.extras
import pandas as pd
import json
import io
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from apontamentos_pplug_jarinu import atualizar_apontamentos
from itsdangerous import URLSafeTimedSerializer
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse

# Verificar se arquivo .env existe
if not os.path.exists('.env'):
    # Tentar encontrar .env em locais alternativos
    possible_paths = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'),
        os.path.join(os.getcwd(), '.env'),
        '.env'
    ]
    
    env_found = False
    for path in possible_paths:
        if os.path.exists(path):
            os.environ['DOTENV_PATH'] = path
            env_found = True
            break
    
    if not env_found:
        print("ERRO: Arquivo .env não encontrado!")
        print("Certifique-se que o arquivo .env está na mesma pasta do executável.")
        input("Pressione Enter para sair...")
        exit(1)

# Carregar .env do caminho correto
if 'DOTENV_PATH' in os.environ:
    load_dotenv(os.environ['DOTENV_PATH'])
else:
    load_dotenv()

app = Flask(__name__)
app.secret_key = 'opera_pu_system_2024'
app.permanent_session_lifetime = timedelta(days=365)

# Configurações para servidor
app.config['JSON_AS_ASCII'] = False
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    response.headers.add('Cache-Control', 'no-cache, no-store, must-revalidate')
    response.headers.add('Pragma', 'no-cache')
    response.headers.add('Expires', '0')
    return response

# Configuração Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Configuração do banco PostgreSQL
DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PSW'),
    'port': os.getenv('DB_PORT'),
    'database': os.getenv('DB_NAME')
}

# Configurações de SSO para integração com o App Acompanhamento de corte
SSO_SHARED_SECRET = os.getenv('SSO_SHARED_SECRET')
SSO_SALT = os.getenv('SSO_SALT', 'app-pu-acomp-sso')
ACOMP_CORTE_BASE_URL = os.getenv('ACOMP_CORTE_BASE_URL', 'http://10.150.16.54:5555')
ACOMP_CORTE_SSO_URL = os.getenv('ACOMP_CORTE_SSO_URL') or f"{ACOMP_CORTE_BASE_URL.rstrip('/')}/sso-login"
ACOMP_CORTE_FALLBACK_URL = os.getenv('ACOMP_CORTE_FALLBACK_URL') or f"{ACOMP_CORTE_BASE_URL.rstrip('/')}/"
ACOMP_CORTE_SSO_LOGOUT_URL = os.getenv('ACOMP_CORTE_SSO_LOGOUT_URL') or f"{ACOMP_CORTE_BASE_URL.rstrip('/')}/sso-logout"
ACOMP_CORTE_DEFAULT_NEXT = os.getenv('ACOMP_CORTE_DEFAULT_NEXT', '/')


@app.context_processor
def inject_acomp_urls():
    return {
        'ACOMP_CORTE_LOGOUT_URL': ACOMP_CORTE_SSO_LOGOUT_URL
    }

# Verificar se todas as variáveis foram carregadas
if not all(DB_CONFIG.values()):
    print("ERRO: Variáveis de ambiente do banco não configuradas!")
    print(f"Valores carregados: {DB_CONFIG}")
    input("Pressione Enter para sair...")
    exit(1)

print("Configurações carregadas com sucesso!")
print(f"Conectando ao banco: {DB_CONFIG['host']}")

def _get_sso_serializer():
    if not SSO_SHARED_SECRET:
        return None
    return URLSafeTimedSerializer(SSO_SHARED_SECRET)


def _append_query_params(base_url, params):
    parts = list(urlparse(base_url))
    query = dict(parse_qsl(parts[4], keep_blank_values=True))
    for key, value in params.items():
        if value is not None:
            query[key] = value
    parts[4] = urlencode(query)
    return urlunparse(parts)


def _build_sso_redirect(user):
    serializer = _get_sso_serializer()
    if not serializer:
        return None
    payload = {
        'id': user.id,
        'usuario': getattr(user, 'username', ''),
        'setor': getattr(user, 'setor', ''),
        'funcao': getattr(user, 'role', ''),
        'iat': datetime.utcnow().isoformat()
    }
    token = serializer.dumps(payload, salt=SSO_SALT)
    target_url = ACOMP_CORTE_SSO_URL or ACOMP_CORTE_FALLBACK_URL
    return _append_query_params(target_url, {
        'token': token,
        'next': ACOMP_CORTE_DEFAULT_NEXT
    })

def enviar_email_credenciais(email_destino, usuario, senha):
    """Envia email com credenciais do usuário"""
    try:
        email_remetente = os.getenv('EMAIL_REMETENTE')
        senha_remetente = os.getenv('EMAIL_SENHA')
        
        if not email_remetente or not senha_remetente:
            print("ERRO: EMAIL_REMETENTE ou EMAIL_SENHA não configurados no .env")
            return
        
        print(f"Tentando enviar email de {email_remetente} para {email_destino}")
        
        # Configurar SMTP para Office 365
        smtp_server = "smtp.office365.com"
        smtp_port = 587
        
        msg = MIMEMultipart()
        msg['From'] = email_remetente
        msg['To'] = email_destino
        msg['Subject'] = "Credenciais de Acesso - Sistema Alocação PU"
        
        corpo_email = f"""Olá!

Suas credenciais de acesso ao Sistema de Alocação de PU foram criadas:

Usuário: {usuario}
Senha: {senha}

Acesse o sistema em: http://localhost:9996

Atenciosamente,
Equipe T.I Opera"""
        
        msg.attach(MIMEText(corpo_email, 'plain', 'utf-8'))
        
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.set_debuglevel(1)  # Debug SMTP
        server.starttls()
        server.login(email_remetente, senha_remetente)
        server.send_message(msg)
        server.quit()
        
        print(f"Email enviado com sucesso para {email_destino}")
        
    except Exception as e:
        print(f"Erro detalhado ao enviar email: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()



class User(UserMixin):
    def __init__(self, id, usuario, funcao, setor):
        self.id = id
        self.username = usuario
        self.role = funcao
        self.setor = setor

@login_manager.user_loader
def load_user(user_id):
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT * FROM public.users WHERE id = %s", (user_id,))
    user_data = cur.fetchone()
    conn.close()
    
    if user_data:
        return User(user_data['id'], user_data['usuario'], user_data['funcao'], user_data.get('setor', ''))
    return None

def get_db_connection():
    # Adicionar configurações de timeout para evitar travamentos
    config = DB_CONFIG.copy()
    config['connect_timeout'] = 10
    config['options'] = '-c statement_timeout=30000 -c timezone=America/Sao_Paulo'  # 30 segundos e timezone brasileiro
    return psycopg2.connect(**config)

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login_post():
    username = request.form['username']
    password = request.form['password']
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT * FROM public.users WHERE usuario = %s", (username,))
    user_data = cur.fetchone()
    conn.close()
    
    if user_data and check_password_hash(user_data['senha'], password):
        user = User(user_data['id'], user_data['usuario'], user_data['funcao'], user_data.get('setor', ''))
        login_user(user, remember=True, duration=timedelta(days=365))
        return redirect(url_for('index'))
    
    flash('Usuário ou senha inválidos')
    return redirect(url_for('login'))


@app.route('/redir/acomp-corte')
@login_required
def redirecionar_acompanhamento_corte():
    redirect_url = _build_sso_redirect(current_user)
    if redirect_url:
        return redirect(redirect_url)
    flash('SSO para o acompanhamento de corte não está configurado. Abrindo endereço padrão.', 'warning')
    return redirect(ACOMP_CORTE_FALLBACK_URL)


@app.route('/register')
@login_required
def register():
    if current_user.setor != 'T.I':
        return redirect(url_for('index'))
    return render_template('register.html')

@app.route('/api/usuarios')
@login_required
def api_usuarios():
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        cur.execute("SELECT id, usuario, funcao, setor FROM public.users WHERE sistema = 'PU' ORDER BY id DESC")
        dados = cur.fetchall()
        conn.close()
        
        return jsonify([dict(row) for row in dados])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/cadastrar-usuario', methods=['POST'])
@login_required
def cadastrar_usuario():
    if current_user.setor != 'T.I':
        return jsonify({'success': False, 'message': 'Acesso negado'}), 403
    
    try:
        dados = request.get_json()
        username = dados.get('username', '').strip()
        password = dados.get('password', '').strip()
        role = dados.get('role', '').strip()
        setor = dados.get('setor', '').strip()
        email = dados.get('email', '').strip()
        
        if not all([username, password, role, setor, email]):
            return jsonify({'success': False, 'message': 'Todos os campos são obrigatórios'})
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Verificar se usuário já existe
        cur.execute("SELECT id FROM public.users WHERE usuario = %s", (username,))
        if cur.fetchone():
            conn.close()
            return jsonify({'success': False, 'message': 'Usuário já existe'})
        
        # Criar usuário
        hashed_password = generate_password_hash(password)
        cur.execute(
            "INSERT INTO public.users (usuario, senha, funcao, setor, email) VALUES (%s, %s, %s, %s, %s)",
            (username, hashed_password, role, setor, email)
        )
        conn.commit()
        conn.close()
        
        # Enviar email
        enviar_email_credenciais(email, username, password)
        
        return jsonify({'success': True, 'message': 'Usuário cadastrado e email enviado com sucesso!'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'}), 500

@app.route('/api/resetar-senha/<int:user_id>', methods=['PUT'])
@login_required
def resetar_senha(user_id):
    if current_user.setor != 'T.I':
        return jsonify({'success': False, 'message': 'Acesso negado'}), 403
    
    try:
        dados = request.get_json()
        nova_senha = dados.get('senha', '').strip()
        
        if not nova_senha:
            return jsonify({'success': False, 'message': 'Nova senha é obrigatória'})
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        hashed_password = generate_password_hash(nova_senha)
        cur.execute(
            "UPDATE public.users SET senha = %s WHERE id = %s",
            (hashed_password, user_id)
        )
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Senha resetada com sucesso!'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'}), 500

@app.route('/api/editar-usuario/<int:user_id>', methods=['PUT'])
@login_required
def editar_usuario(user_id):
    if current_user.setor != 'T.I':
        return jsonify({'success': False, 'message': 'Acesso negado'}), 403
    
    try:
        dados = request.get_json()
        usuario = dados.get('usuario', '').strip()
        funcao = dados.get('funcao', '').strip()
        setor = dados.get('setor', '').strip()
        
        if not all([usuario, funcao, setor]):
            return jsonify({'success': False, 'message': 'Usuário, função e setor são obrigatórios'})
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute(
            "UPDATE public.users SET usuario = %s, funcao = %s, setor = %s WHERE id = %s",
            (usuario, funcao, setor, user_id)
        )
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Usuário atualizado com sucesso!'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'}), 500

@app.route('/api/excluir-usuario/<int:user_id>', methods=['DELETE'])
@login_required
def excluir_usuario(user_id):
    if current_user.setor != 'T.I':
        return jsonify({'success': False, 'message': 'Acesso negado'}), 403
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("DELETE FROM public.users WHERE id = %s", (user_id,))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Usuário excluído com sucesso!'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'}), 500



@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/index')
@login_required
def index():
    if current_user.setor == 'Produção':
        return redirect(url_for('otimizadas'))
    if current_user.setor not in ['Administrativo', 'T.I']:
        return redirect(url_for('otimizadas'))
    return render_template('index.html')

@app.route('/estoque')
@login_required
def estoque():
    if current_user.setor not in ['Produção', 'Administrativo', 'T.I']:
        return redirect(url_for('index'))
    return render_template('estoque.html')

@app.route('/consulta-estoque')
@login_required
def consulta_estoque():
    if current_user.setor not in ['Produção', 'Administrativo', 'T.I']:
        return redirect(url_for('index'))
    return render_template('consulta_estoque.html')

@app.route('/dashboard-producao')
@login_required
def dashboard_producao():
    if current_user.setor not in ['Produção', 'Administrativo', 'T.I']:
        return redirect(url_for('index'))
    return render_template('dashboard_producao.html')

@app.route('/locais')
@login_required
def locais():
    if current_user.setor not in ['Produção', 'Administrativo', 'T.I']:
        return redirect(url_for('index'))
    return render_template('locais.html')

@app.route('/otimizadas')
@login_required
def otimizadas():
    if current_user.setor not in ['Produção', 'Administrativo', 'T.I']:
        return redirect(url_for('index'))
    return render_template('otimizadas.html')

@app.route('/saidas')
@login_required
def saidas():
    if current_user.setor not in ['Administrativo', 'T.I']:
        return redirect(url_for('otimizadas'))
    return render_template('saidas.html')

@app.route('/saidas-exit')
@login_required
def saidas_exit():
    if current_user.setor not in ['Administrativo', 'T.I']:
        return redirect(url_for('otimizadas'))
    return render_template('saidas_exit.html')

@app.route('/arquivos')
@login_required
def arquivos():
    if current_user.setor not in ['Administrativo', 'T.I']:
        return redirect(url_for('otimizadas'))
    return render_template('arquivos.html')

@app.route('/relatorio')
@login_required
def relatorio():
    if current_user.setor not in ['Produção', 'Administrativo', 'T.I']:
        return redirect(url_for('otimizadas'))
    return render_template('relatorio.html')



@app.route('/etiquetas')
@login_required
def etiquetas():
    if current_user.setor == 'Produção':
        return redirect(url_for('otimizadas'))
    return render_template('etiquetas.html')

@app.route('/api/importar-etiquetas', methods=['POST', 'OPTIONS'])
@login_required
def importar_etiquetas():
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        return response
        
    try:
        if 'file' not in request.files:
            response = jsonify({'success': False, 'message': 'Nenhum arquivo enviado'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response
        
        file = request.files['file']
        if file.filename == '':
            response = jsonify({'success': False, 'message': 'Nenhum arquivo selecionado'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response
        
        # Ler Excel com engine específico
        try:
            df = pd.read_excel(file, engine='openpyxl')
        except Exception as excel_error:
            response = jsonify({'success': False, 'message': f'Erro ao ler arquivo Excel: {str(excel_error)}'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response
        
        # Verificar se tem dados
        if df.empty:
            response = jsonify({'success': False, 'message': 'Arquivo vazio'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response
        
        # Processar apenas primeiras 3 linhas para teste
        dados_processados = []
        for i, row in df.head(3).iterrows():
            dados_processados.append({
                'id': str(row.get('ID', i)),
                'veiculo': str(row.get('Veiculo', 'Teste')),
                'op': str(row.get('OP', '123')),
                'peca': 'TSP',
                'descricao': str(row.get('Descrição', 'Teste')),
                'camada': 'L3',
                'quantidade_etiquetas': 1
            })
        
        return jsonify({'success': True, 'dados': dados_processados})
        
    except Exception as e:
        response = jsonify({'success': False, 'message': f'Erro: {str(e)}'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@app.route('/api/gerar-etiquetas-pdf', methods=['POST'])
@login_required
def gerar_etiquetas_pdf():
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        from datetime import datetime
        import tempfile
        import os
        
        dados = request.get_json().get('dados', [])
        
        if not dados:
            return jsonify({'success': False, 'message': 'Nenhum dado fornecido'})
        
        # Criar PDF em memória com tamanho personalizado para etiquetas
        buffer = io.BytesIO()
        etiqueta_width = 100*mm
        etiqueta_height = 50*mm
        
        # Usar tamanho da página igual ao da etiqueta
        c = canvas.Canvas(buffer, pagesize=(etiqueta_width, etiqueta_height))
        width, height = etiqueta_width, etiqueta_height
        
        x_pos = 0
        y_pos = 0
        
        primeira_etiqueta = True
        for item in dados:
            for i in range(item['quantidade_etiquetas']):
                # Nova página para cada etiqueta (exceto a primeira)
                if not primeira_etiqueta:
                    c.showPage()
                primeira_etiqueta = False
                
                # Desenhar etiqueta ocupando toda a página
                desenhar_etiqueta_simples(c, 0, 0, width, height, {
                    'OP': item['op'],
                    'Peca': item['peca'],
                    'Veiculo': item['veiculo'],
                    'Descricao': item.get('descricao', ''),
                    'ID': item['id']
                })
        
        c.save()
        buffer.seek(0)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'etiquetas_{timestamp}.pdf'
        
        return send_file(
            buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'})

def desenhar_etiqueta_simples(c, x, y, width, height, dados):
    from reportlab.lib.units import mm
    from datetime import datetime
    
    # Desenhar borda externa
    c.setStrokeColorRGB(0, 0, 0)
    c.setLineWidth(1)
    c.rect(x + 1*mm, y + 1*mm, width - 2*mm, height - 2*mm)
    
    # Título PU no canto superior esquerdo
    c.setFont("Helvetica-Bold", 12)
    c.drawString(x + 3*mm, y + height - 6*mm, "PU")
    
    # Data atual no canto superior direito
    data_atual = datetime.now().strftime("%d/%m/%Y")
    c.setFont("Helvetica-Bold", 10)
    c.drawString(x + width - 25*mm, y + height - 6*mm, data_atual)
    
    # OP na linha principal (maior)
    y_pos = y + height - 15*mm
    c.setFont("Helvetica-Bold", 14)
    c.drawString(x + 3*mm, y_pos, "OP:")
    c.setFont("Helvetica-Bold", 24)
    c.drawString(x + 15*mm, y_pos, f"{dados['OP']}")
    
    # CARRO (mais acima)
    y_pos -= 6*mm
    c.setFont("Helvetica-Bold", 10)
    c.drawString(x + 3*mm, y_pos, "CARRO:")
    c.setFont("Helvetica-Bold", 10)
    c.drawString(x + 20*mm, y_pos, f"{dados['Veiculo']}")
    
    # ID na linha abaixo do carro (maior)
    y_pos -= 6*mm
    c.setFont("Helvetica-Bold", 12)
    c.drawString(x + 3*mm, y_pos, "ID:")
    c.setFont("Helvetica-Bold", 18)
    c.drawString(x + 15*mm, y_pos, f"{dados['ID']}")
    
    # DESCRIÇÃO abaixo da camada (grande)
    y_pos -= 8*mm
    c.setFont("Helvetica-Bold", 22)
    descricao = dados.get('Descricao', '')
    if len(descricao) > 30:
        descricao = descricao[:30] + '...'
    c.drawString(x + 3*mm, y_pos, descricao)
    
    # Código de barras Code128
    codigo_barras_texto = f"{dados['Peca']}{dados['OP']}"
    
    try:
        import barcode
        from barcode.writer import ImageWriter
        import tempfile
        import os
        
        # Configurar writer sem texto
        writer = ImageWriter()
        writer.quiet_zone = 3
        writer.font_size = 0
        writer.text_distance = 0
        writer.write_text = False
        
        # Gerar código de barras Code128 sem texto
        codigo_barras_obj = barcode.get('code128', codigo_barras_texto, writer=writer)
        codigo_barras_obj.default_writer_options['write_text'] = False
        
        # Salvar código de barras temporariamente
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_barcode:
            img_barcode = codigo_barras_obj.render()
            img_barcode.save(tmp_barcode.name, 'PNG')
            tmp_barcode.close()
            
            # Inserir código de barras na parte inferior ocupando toda a largura
            c.drawImage(tmp_barcode.name, x + 2*mm, y + 1*mm, width=width-4*mm, height=10*mm)
            
            # Limpar arquivo temporário
            try:
                os.remove(tmp_barcode.name)
            except:
                pass
                
    except Exception as e:
        # Fallback: texto simples se código de barras falhar
        c.setFont("Courier", 8)
        c.drawString(x + 3*mm, y + 3*mm, codigo_barras_texto)

def verificar_e_atualizar_status_lote(lote_vd, lote_pu, cur):
    """Verifica se todas as peças do lote estão no estoque e atualiza status para CORTADO"""
    try:
        if not lote_vd:
            return False
            
        # Contar total de peças do lote na tabela plano_controle_corte_vidro2
        cur.execute("""
            SELECT COUNT(*) FROM public.plano_controle_corte_vidro2
            WHERE id_lote = %s
        """, (lote_vd,))
        total_pecas_lote = cur.fetchone()[0]
        
        if total_pecas_lote == 0:
            return False
            
        # Contar peças do lote que estão no estoque
        cur.execute("""
            SELECT COUNT(*) FROM public.pu_inventory
            WHERE lote_vd = %s OR lote_pu = %s
        """, (lote_vd, lote_pu))
        pecas_no_estoque = cur.fetchone()[0]
        
        # Se todas as peças do lote estão no estoque, marcar como CORTADO
        if pecas_no_estoque >= total_pecas_lote:
            cur.execute("""
                UPDATE public.plano_controle_corte_vidro2 
                SET pu_cortado = 'CORTADO'
                WHERE id_lote = %s
            """, (lote_vd,))
            print(f"DEBUG: Lote {lote_vd} marcado como CORTADO ({pecas_no_estoque}/{total_pecas_lote} peças no estoque)")
            return True
        else:
            print(f"DEBUG: Lote {lote_vd} ainda não está completo ({pecas_no_estoque}/{total_pecas_lote} peças no estoque)")
            return False
            
    except Exception as e:
        print(f"DEBUG: Erro ao verificar status do lote {lote_vd}: {e}")
        return False

def sugerir_local_armazenamento(tipo_peca, locais_ocupados, conn):
    """Sugere local de armazenamento preenchendo horizontalmente E1, F1, G1..."""
    
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Buscar locais ativos no banco
        cur.execute("SELECT local, nome FROM public.pu_locais WHERE status = 'Ativo' ORDER BY local")
        locais_ativos = cur.fetchall()
        
        if not locais_ativos:
            return 'E1', 'COLMEIA'
        
        # Buscar locais que já têm peças diferentes do tipo atual
        cur.execute("""
            SELECT DISTINCT local FROM public.pu_inventory 
            WHERE peca != %s AND local IS NOT NULL AND local != ''
            UNION
            SELECT DISTINCT local FROM public.pu_otimizadas 
            WHERE peca != %s AND tipo = 'PU' AND local IS NOT NULL AND local != ''
        """, (tipo_peca, tipo_peca))
        locais_com_pecas_diferentes = {row['local'] for row in cur.fetchall()}
        
        # Criar mapeamento de locais por rack
        locais_por_rack = {}
        for local_info in locais_ativos:
            local = local_info['local']
            rack = local_info['nome']
            if rack not in locais_por_rack:
                locais_por_rack[rack] = []
            locais_por_rack[rack].append(local)
        
        # Ordenar locais por número para cada rack
        for rack in locais_por_rack:
            locais_por_rack[rack].sort(key=lambda x: (int(''.join(filter(str.isdigit, x))), x[0]))
        
        # Sequência de preenchimento horizontal: E1, F1, G1... depois E2, F2, G2...
        def gerar_sequencia_horizontal():
            sequencia = []
            
            # Determinar range de números para cada rack
            ranges_rack = {
                'RACK1': range(1, 29),
                'RACK2': range(29, 57), 
                'RACK3': range(57, 85)
            }
            
            # Para cada rack
            for rack_name in ['RACK1', 'RACK2', 'RACK3']:
                if rack_name not in locais_por_rack:
                    continue
                    
                num_range = ranges_rack[rack_name]
                
                # Primeiro preencher todas as colunas E até M
                for num in num_range:
                    for letra_code in range(ord('E'), ord('M') + 1):
                        letra = chr(letra_code)
                        local = f"{letra}{num}"
                        
                        if local in locais_por_rack[rack_name]:
                            sequencia.append((local, 'COLMEIA'))
                
                # Depois preencher D até A (só depois de terminar E-M)
                for num in num_range:
                    for letra_code in range(ord('D'), ord('A') - 1, -1):
                        letra = chr(letra_code)
                        local = f"{letra}{num}"
                        
                        if local in locais_por_rack[rack_name]:
                            sequencia.append((local, 'COLMEIA'))
            
            return sequencia
        
        sequencia_completa = gerar_sequencia_horizontal()
        
        # Combinar locais ocupados com locais que têm peças diferentes
        locais_bloqueados = locais_ocupados | locais_com_pecas_diferentes
        
        # Buscar primeiro local disponível
        for local, rack in sequencia_completa:
            if local not in locais_bloqueados:
                # Verificar novamente se o local não foi ocupado por outra thread/processo
                cur.execute("""
                    SELECT COUNT(*) FROM (
                        SELECT local FROM public.pu_inventory WHERE local = %s
                        UNION ALL
                        SELECT local FROM public.pu_otimizadas WHERE local = %s AND tipo = 'PU'
                        UNION ALL
                        SELECT local FROM public.pu_manuais WHERE local = %s
                    ) AS occupied
                """, (local, local, local))
                
                if cur.fetchone()[0] == 0:
                    return local, rack
        
        # Se não encontrou nenhum disponível, retornar None para indicar erro
        return None, None
        
    except Exception as e:
        print(f"DEBUG: Erro na sugestão de local: {e}")
        return 'E1', 'COLMEIA'

@app.route('/api/adicionar-peca-manual', methods=['POST'])
@login_required
def adicionar_peca_manual():
    dados = request.get_json()
    op = dados.get('op', '').strip()
    peca = dados.get('peca', '').strip()
    projeto = dados.get('projeto', '').strip()
    veiculo = dados.get('veiculo', '').strip()
    sensor = dados.get('sensor', '').strip()
    
    if not all([op, peca, projeto, veiculo]):
        return jsonify({'success': False, 'message': 'Todos os campos são obrigatórios'})
    
    if peca == 'PBS' and not sensor:
        return jsonify({'success': False, 'message': 'Sensor é obrigatório para peças PBS'})
    
    try:
        # Verificar se peça já existe
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        cur.execute("SELECT COUNT(*) FROM public.pu_inventory WHERE op = %s AND peca = %s", (op, peca))
        existe_estoque = cur.fetchone()[0] > 0
        
        cur.execute("SELECT COUNT(*) FROM public.pu_otimizadas WHERE op = %s AND peca = %s AND tipo = 'PU'", (op, peca))
        existe_otimizadas = cur.fetchone()[0] > 0
        
        cur.execute("SELECT COUNT(*) FROM public.pu_manuais WHERE op = %s AND peca = %s", (op, peca))
        existe_manuais = cur.fetchone()[0] > 0
        
        conn.close()
        
        if existe_estoque or existe_otimizadas or existe_manuais:
            return jsonify({'success': False, 'message': f'Peça {peca} com OP {op} já existe no sistema'})
    
    except Exception as e:
        print(f"Erro na verificação: {e}")
    
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Criar tabela se não existir
        cur.execute("""
            CREATE TABLE IF NOT EXISTS public.pu_manuais (
                id SERIAL PRIMARY KEY,
                op TEXT,
                peca TEXT,
                projeto TEXT,
                veiculo TEXT,
                local TEXT,
                rack TEXT,
                arquivo TEXT,
                usuario TEXT,
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Buscar TODOS os locais ocupados (incluindo manuais)
        cur.execute("""
            SELECT local FROM public.pu_inventory WHERE local IS NOT NULL AND local != '' 
            UNION 
            SELECT local FROM public.pu_otimizadas WHERE tipo = 'PU' AND local IS NOT NULL AND local != ''
            UNION
            SELECT local FROM public.pu_manuais WHERE local IS NOT NULL AND local != ''
        """)
        locais_ocupados = {row['local'] for row in cur.fetchall()}
        
        # Buscar locais que já têm peças diferentes do tipo atual
        cur.execute("""
            SELECT DISTINCT local FROM public.pu_inventory 
            WHERE peca != %s AND local IS NOT NULL AND local != ''
            UNION
            SELECT DISTINCT local FROM public.pu_otimizadas 
            WHERE peca != %s AND tipo = 'PU' AND local IS NOT NULL AND local != ''
            UNION
            SELECT DISTINCT local FROM public.pu_manuais 
            WHERE peca != %s AND local IS NOT NULL AND local != ''
        """, (peca, peca, peca))
        locais_com_pecas_diferentes = {row['local'] for row in cur.fetchall()}
        
        # Combinar todos os locais bloqueados
        locais_bloqueados = locais_ocupados | locais_com_pecas_diferentes
        
        # Buscar arquivo baseado no projeto, peça e sensor
        arquivo_status = "Sem arquivo"
        if peca == 'PBS' and sensor:
            cur.execute("""
                SELECT nome_peca FROM public.arquivos_pu
                WHERE projeto = %s AND peca = %s AND sensor = %s
                LIMIT 1
            """, (projeto, peca, sensor))
            arquivo_result = cur.fetchone()
            if arquivo_result:
                arquivo_status = arquivo_result['nome_peca']
        else:
            # Fallback para busca tradicional
            cur.execute("""
                SELECT nome_peca FROM public.arquivos_pu
                WHERE projeto = %s AND peca = %s
                LIMIT 1
            """, (projeto, peca))
            arquivo_result = cur.fetchone()
            if arquivo_result:
                arquivo_status = arquivo_result['nome_peca']
        
        # Sugerir local (passando locais bloqueados)
        local_sugerido, rack_sugerido = sugerir_local_armazenamento(peca, locais_bloqueados, conn)
        
        # Verificar se conseguiu sugerir um local válido
        if not local_sugerido or not rack_sugerido:
            conn.close()
            return jsonify({'success': False, 'message': 'Não há locais disponíveis para esta peça'}), 400
        
        # Buscar lote da peça na tabela plano_controle_corte_vidro2
        lote_vd = ''
        lote_pu = ''
        cur.execute("""
            SELECT id_lote FROM public.plano_controle_corte_vidro2
            WHERE op = %s AND peca = %s
            LIMIT 1
        """, (op, peca))
        lote_result = cur.fetchone()
        if lote_result and lote_result['id_lote']:
            lote_vd = lote_result['id_lote']
            lote_pu = 'PU' + lote_vd[2:] if len(lote_vd) >= 2 else lote_vd
        
        # Adicionar colunas lote_vd e lote_pu se não existirem na tabela pu_manuais
        try:
            cur.execute("ALTER TABLE public.pu_manuais ADD COLUMN IF NOT EXISTS lote_vd TEXT")
            cur.execute("ALTER TABLE public.pu_manuais ADD COLUMN IF NOT EXISTS lote_pu TEXT")
        except:
            pass
        
        # Inserir na tabela pu_manuais
        cur.execute("""
            INSERT INTO public.pu_manuais (op, peca, projeto, veiculo, local, rack, arquivo, usuario, lote_vd, lote_pu)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (op, peca, projeto, veiculo, local_sugerido, rack_sugerido, arquivo_status, current_user.username, lote_vd, lote_pu))
        
        # Log da ação
        cur.execute("""
            INSERT INTO public.pu_logs (usuario, acao, detalhes, data_acao)
            VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
        """, (
            current_user.username,
            'ADICAO_MANUAL',
            f'Adicionou peça {peca} - OP {op} manualmente'
        ))
        
        conn.commit()
        conn.close()
        
        response_data = {
            'success': True, 
            'message': 'Peça adicionada com sucesso!',
            'peca': {
                'op': op,
                'peca': peca,
                'projeto': projeto,
                'veiculo': veiculo,
                'local': local_sugerido,
                'rack': rack_sugerido,
                'arquivo_status': arquivo_status,
                'sensor': sensor
            }
        }
        
        response = make_response(jsonify(response_data))
        response.headers['Content-Type'] = 'application/json; charset=utf-8'
        return response
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'}), 500

@app.route('/api/atualizar-apontamentos', methods=['POST'])
@login_required
def api_atualizar_apontamentos():
    try:
        resultado = atualizar_apontamentos()
        return jsonify(resultado)
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro ao atualizar apontamentos: {str(e)}'}), 500

@app.route('/api/lotes', methods=['GET'])
@login_required
def get_lotes():
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Buscar lotes únicos com data e turno
        cur.execute("""
            SELECT DISTINCT id_lote, data_programacao, turno_programacao
            FROM public.plano_controle_corte_vidro2 
            WHERE status = 'PROGRAMADO' 
            AND (pu_cortado IS NULL OR pu_cortado = '' OR pu_cortado = 'PROGRAMANDO')
            AND (etapa_baixa IS NULL OR etapa_baixa = '' OR etapa_baixa = 'INSPECAO FINAL' OR etapa_baixa = 'RT-RP')
            ORDER BY data_programacao DESC, turno_programacao, id_lote
        """)
        
        rows = cur.fetchall()
        print(f"DEBUG: Encontrados {len(rows)} lotes")
        
        lotes = []
        for row in rows:
            # Converter turno para formato desejado
            turno_map = {
                'primeiro': '1°',
                'segundo': '2°', 
                'terceiro': '3°'
            }
            turno_formatado = turno_map.get(row['turno_programacao'], row['turno_programacao'])
            
            # Converter data para formato brasileiro
            data_obj = row['data_programacao']
            if isinstance(data_obj, str):
                from datetime import datetime
                data_obj = datetime.strptime(data_obj, '%Y-%m-%d').date()
            data_formatada = data_obj.strftime('%d/%m/%Y')
            
            lotes.append({
                'id_lote': row['id_lote'],
                'display': f"{turno_formatado} - {data_formatada} - {row['id_lote']}",
                'data_programacao': row['data_programacao'],
                'turno_programacao': row['turno_programacao']
            })
        
        conn.close()
        return jsonify(lotes)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/dados')
def api_dados():
    lote = request.args.get('lote', '')
    
    print(f"DEBUG: Buscando dados - lote: {lote}")
    
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Verificar se a tabela existe
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'plano_controle_corte_vidro2'
            )
        """)
        tabela_existe = cur.fetchone()[0]
        
        if not tabela_existe:
            print("DEBUG: Tabela public.plano_controle_corte_vidro2 não existe")
            conn.close()
            return jsonify([])
        
        # Buscar peças já existentes no estoque, otimizadas e manuais
        cur.execute("SELECT op, peca FROM public.pu_inventory")
        pecas_estoque = cur.fetchall()
        
        cur.execute("SELECT op, peca FROM public.pu_otimizadas WHERE tipo = 'PU'")
        pecas_otimizadas = cur.fetchall()
        
        cur.execute("SELECT op, peca FROM public.pu_manuais")
        pecas_manuais = cur.fetchall()
        
        # Buscar TODOS os locais ocupados (incluindo os já otimizados)
        cur.execute("SELECT local FROM public.pu_inventory WHERE local IS NOT NULL AND local != '' UNION SELECT local FROM public.pu_otimizadas WHERE tipo = 'PU' AND local IS NOT NULL AND local != ''")
        locais_ocupados_fixos = {row['local'] for row in cur.fetchall()}
        
        # Verificar se há locais disponíveis
        cur.execute("SELECT COUNT(*) FROM public.pu_locais WHERE status = 'Ativo'")
        total_locais = cur.fetchone()[0]
        
        if len(locais_ocupados_fixos) >= total_locais:
            conn.close()
            return jsonify({'error': 'Não há locais disponíveis. Todos os locais estão ocupados.'}), 400
        
        # Criar set para busca rápida
        pecas_existentes = {f"{row['op']}_{row['peca']}" for row in pecas_estoque}
        pecas_existentes.update({f"{row['op']}_{row['peca']}" for row in pecas_otimizadas})
        pecas_existentes.update({f"{row['op']}_{row['peca']}" for row in pecas_manuais})
        
        # Atualizar status para PROGRAMANDO ao coletar dados
        cur.execute("""
            UPDATE public.plano_controle_corte_vidro2 
            SET pu_cortado = 'PROGRAMANDO'
            WHERE id_lote = %s
        """, (lote,))
        conn.commit()
        
        # Query da nova tabela plano_controle_corte_vidro2
        query = """
            SELECT op, peca, projeto, id_lote
            FROM public.plano_controle_corte_vidro2 
            WHERE id_lote = %s
            AND status = 'PROGRAMADO'
            AND (pu_cortado IS NULL OR pu_cortado = '' OR pu_cortado = 'PROGRAMANDO')
            AND (etapa_baixa IS NULL OR etapa_baixa = '' OR etapa_baixa = 'INSPECAO FINAL' OR etapa_baixa = 'RT-RP')
            ORDER BY op DESC
        """
        params = [lote]
        
        print(f"DEBUG: Query: {query}")
        print(f"DEBUG: Params: {params}")
        
        cur.execute(query, params)
        dados_banco = cur.fetchall()
        
        print(f"DEBUG: Encontrados {len(dados_banco)} registros no banco")
        
        # Processar dados do banco
        dados_filtrados = []
        locais_usados_nesta_sessao = set()
        
        for row in dados_banco:
            try:
                chave_peca = f"{row['op']}_{row['peca']}"
                if chave_peca not in pecas_existentes:
                    # Combinar locais ocupados com os já usados nesta sessão
                    locais_bloqueados = locais_ocupados_fixos | locais_usados_nesta_sessao
                    
                    # Aplicar lógica de sugestão
                    local_sugerido, rack_sugerido = sugerir_local_armazenamento(row['peca'], locais_bloqueados, conn)
                    
                    # Se não conseguiu sugerir local, usar "SEM LOCAL"
                    if not local_sugerido or not rack_sugerido or local_sugerido in locais_usados_nesta_sessao:
                        local_sugerido = "SEM LOCAL"
                        rack_sugerido = "N/A"
                        print(f"DEBUG: Não foi possível sugerir local para peça {row['peca']}, usando SEM LOCAL")
                    
                    # Buscar arquivo baseado no projeto e peça
                    arquivo_status = 'Sem arquivo de corte'
                    
                    cur.execute("""
                        SELECT nome_peca FROM public.arquivos_pu
                        WHERE projeto = %s AND peca = %s
                        LIMIT 1
                    """, (str(row['projeto']) if row['projeto'] else '', row['peca']))
                    arquivo_result = cur.fetchone()
                    if arquivo_result:
                        arquivo_status = arquivo_result['nome_peca']
                    
                    # Buscar veículo na tabela dados_uso_geral.dados_op usando OP
                    veiculo = ''
                    cur.execute("""
                        SELECT modelo FROM dados_uso_geral.dados_op 
                        WHERE op::text = %s AND planta = 'Jarinu'
                        LIMIT 1
                    """, (str(row['op']) if row['op'] else '',))
                    veiculo_result = cur.fetchone()
                    if veiculo_result and veiculo_result['modelo']:
                        # Extrair apenas o nome do veículo (remover código do projeto)
                        modelo_completo = veiculo_result['modelo']
                        partes = modelo_completo.split(' ')
                        if len(partes) >= 3:
                            veiculo = ' '.join(partes[2:])  # Pegar tudo após as duas primeiras palavras
                        else:
                            veiculo = modelo_completo
                    
                    # Buscar sensor se a peça for PBS
                    sensor = ''
                    if str(row['peca']) == 'PBS':
                        cur.execute("""
                            SELECT sensor FROM public.arquivos_pu
                            WHERE projeto = %s AND peca = %s
                            LIMIT 1
                        """, (str(row['projeto']) if row['projeto'] else '', str(row['peca'])))
                        sensor_result = cur.fetchone()
                        if sensor_result:
                            sensor = sensor_result['sensor'] or ''
                    
                    item = {
                        'op_pai': '0',
                        'op': str(row['op']) if row['op'] else '',
                        'peca': str(row['peca']) if row['peca'] else '',
                        'projeto': str(row['projeto']) if row['projeto'] else '',
                        'veiculo': veiculo,
                        'local': local_sugerido or '',
                        'rack': rack_sugerido or '',
                        'data_criacao': datetime.now().isoformat(),
                        'arquivo_status': arquivo_status,
                        'sensor': sensor
                    }
                    
                    # Adicionar o local aos usados nesta sessão (apenas se não for "SEM LOCAL")
                    if local_sugerido and local_sugerido != "SEM LOCAL":
                        locais_usados_nesta_sessao.add(local_sugerido)
                    dados_filtrados.append(item)
            except Exception as row_error:
                print(f"DEBUG: Erro ao processar linha: {row_error}")
                if conn:
                    conn.rollback()
                continue
        
        # Adicionar peças manuais
        try:
            cur.execute("SELECT op, peca, projeto, veiculo, local, rack, arquivo FROM public.pu_manuais")
            pecas_manuais_db = cur.fetchall()
        except Exception as manuais_error:
            print(f"DEBUG: Erro ao buscar peças manuais: {manuais_error}")
            if conn:
                conn.rollback()
            pecas_manuais_db = []
        
        for peca_manual in pecas_manuais_db:
            # Buscar sensor se a peça for PBS
            sensor = ''
            if str(peca_manual[1]) == 'PBS':
                cur.execute("""
                    SELECT sensor FROM public.arquivos_pu
                    WHERE projeto = %s AND peca = %s
                    LIMIT 1
                """, (str(peca_manual[2]) if peca_manual[2] else '', str(peca_manual[1])))
                sensor_result = cur.fetchone()
                if sensor_result:
                    sensor = sensor_result['sensor'] or ''
            
            item = {
                'op_pai': '0',
                'op': str(peca_manual[0]) if peca_manual[0] else '',
                'peca': str(peca_manual[1]) if peca_manual[1] else '',
                'projeto': str(peca_manual[2]) if peca_manual[2] else '',
                'veiculo': str(peca_manual[3]) if peca_manual[3] else '',
                'local': peca_manual[4] or '',
                'rack': peca_manual[5] or '',
                'data_criacao': datetime.now().isoformat(),
                'arquivo_status': peca_manual[6] or 'Sem arquivo',
                'sensor': sensor
            }
            dados_filtrados.append(item)
        
        if conn:
            conn.close()
        print(f"DEBUG: Retornando {len(dados_filtrados)} itens filtrados (incluindo {len(pecas_manuais_db)} manuais)")
        return jsonify(dados_filtrados)
        
    except Exception as e:
        print(f"DEBUG: Erro na API dados: {str(e)}")
        if conn:
            conn.rollback()
            conn.close()
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Erro ao buscar dados: {str(e)}'}), 500

@app.route('/api/dashboard-producao')
@login_required
def api_dashboard_producao():
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Verificar se tabela existe
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'pu_inventory'
            )
        """)
        tabela_existe = cur.fetchone()[0]
        
        if not tabela_existe:
            conn.close()
            return jsonify([])
        
        # Query otimizada com LEFT JOIN incluindo prioridade
        cur.execute("""
            SELECT 
                i.op, i.peca, i.projeto, i.veiculo, i.local,
                COALESCE(UPPER(d.etapa), 'IF') as etapa,
                COALESCE(UPPER(d.prioridade), 'NORMAL') as prioridade
            FROM public.pu_inventory i
            LEFT JOIN dados_uso_geral.dados_op d ON i.op::text = d.op::text AND i.peca = d.item AND d.planta = 'Jarinu'
            ORDER BY i.id DESC
        """)
        dados = cur.fetchall()
        
        resultado = []
        for row in dados:
            etapa = row['etapa']
            prioridade = row['prioridade']
            status = 'normal'
            if etapa in ['INSPECAO FINAL', 'BUFFER-AUTOCLAVE', 'AUTOCLAVE', 'EMBOLSADO']:
                status = 'critico'
            elif etapa in ['PRE-MONTAGEM', 'PREMONTAGEM']:
                status = 'aviso'
            elif etapa == 'IF':
                status = 'critico'
            
            resultado.append({
                'op': row['op'] or '',
                'peca': row['peca'] or '',
                'projeto': row['projeto'] or '',
                'veiculo': row['veiculo'] or '',
                'local': row['local'] or '',
                'etapa': etapa,
                'prioridade': prioridade,
                'status': status
            })
        
        conn.close()
        print(f"DEBUG: Dashboard retornando {len(resultado)} itens do estoque")
        return jsonify(resultado)
        
    except Exception as e:
        print(f"ERRO na API dashboard: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/estoque')
def api_estoque():
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Verificar se tabela existe
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'pu_inventory'
            )
        """)
        tabela_existe = cur.fetchone()[0]
        
        if not tabela_existe:
            conn.close()
            return jsonify([])
        
        # Buscar todos os dados
        cur.execute("SELECT id, op_pai, op, peca, projeto, veiculo, local, rack, camada, data, sensor, lote_vd, lote_pu FROM public.pu_inventory ORDER BY id DESC")
        dados = cur.fetchall()
        conn.close()
        
        resultado = []
        for row in dados:
            resultado.append({
                'id': row['id'],
                'op_pai': row['op_pai'] or '',
                'op': row['op'] or '',
                'peca': row['peca'] or '',
                'projeto': row['projeto'] or '',
                'veiculo': row['veiculo'] or '',
                'local': row['local'] or '',
                'rack': row['rack'] or '',
                'camada': row['camada'] or '',
                'data': row['data'].strftime('%d/%m/%Y') if row.get('data') else '',
                'sensor': row.get('sensor') or '',
                'lote_vd': row.get('lote_vd') or '',
                'lote_pu': row.get('lote_pu') or ''
            })
        
        print(f"DEBUG: Retornando {len(resultado)} itens do estoque")
        return jsonify(resultado)
        
    except Exception as e:
        print(f"ERRO na API estoque: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/estoque-data')
def estoque_data():
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Verificar se tabela existe
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'pu_inventory'
            )
        """)
        tabela_existe = cur.fetchone()[0]
        
        if not tabela_existe:
            conn.close()
            return jsonify([])
        
        cur.execute("SELECT id, op_pai, op, peca, projeto, veiculo, local, rack, camada FROM public.pu_inventory ORDER BY id DESC")
        dados = cur.fetchall()
        conn.close()
        return jsonify([dict(row) for row in dados])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/otimizar-pecas', methods=['POST'])
@login_required
def otimizar_pecas():
    conn = None
    try:
        print("DEBUG: Iniciando otimização")
        dados = request.get_json()
        print(f"DEBUG: Dados recebidos: {dados}")
        
        pecas_selecionadas = dados.get('pecas', [])
        print(f"DEBUG: {len(pecas_selecionadas)} peças selecionadas")
        
        if not pecas_selecionadas:
            return jsonify({'success': False, 'message': 'Nenhuma peça selecionada'})
        
        # Verificar se há locais duplicados nas peças selecionadas (excluindo "SEM LOCAL")
        locais_selecionados = [peca.get('local') for peca in pecas_selecionadas if peca.get('local') and peca.get('local') != 'SEM LOCAL']
        locais_duplicados = [local for local in set(locais_selecionados) if locais_selecionados.count(local) > 1]
        
        if locais_duplicados:
            return jsonify({
                'success': False, 
                'message': f'Locais duplicados detectados: {", ".join(locais_duplicados)}. Não é possível otimizar peças com o mesmo local.'
            })
        
        # Verificar se há peças sem local disponível
        pecas_sem_local = [peca for peca in pecas_selecionadas if peca.get('local') == 'SEM LOCAL']
        if pecas_sem_local:
            return jsonify({
                'success': False, 
                'message': f'Existem {len(pecas_sem_local)} peça(s) sem local disponível. Não é possível otimizar.'
            })
        
        print("DEBUG: Conectando ao banco")
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Verificar se os locais das peças selecionadas já estão ocupados no banco
        for peca in pecas_selecionadas:
            local = peca.get('local')
            if local:
                cur.execute("""
                    SELECT COUNT(*) FROM (
                        SELECT local FROM public.pu_inventory WHERE local = %s
                        UNION ALL
                        SELECT local FROM public.pu_otimizadas WHERE local = %s AND tipo = 'PU'
                    ) AS occupied
                """, (local, local))
                
                if cur.fetchone()[0] > 0:
                    conn.close()
                    return jsonify({
                        'success': False, 
                        'message': f'Local {local} já está ocupado no banco de dados. Atualize os dados antes de otimizar.'
                    })
        
        print("DEBUG: Criando tabela se necessário")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS public.pu_otimizadas (
                id SERIAL PRIMARY KEY,
                op_pai TEXT,
                op TEXT,
                peca TEXT,
                projeto TEXT,
                veiculo TEXT,
                local TEXT,
                rack TEXT,
                cortada BOOLEAN DEFAULT FALSE,
                user_otimizacao TEXT,
                data_otimizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                tipo TEXT DEFAULT 'PU',
                camada TEXT,
                lote_vd TEXT,
                lote_pu TEXT
            )
        """)
        
        # Adicionar colunas se não existirem
        try:
            cur.execute("ALTER TABLE public.pu_otimizadas ADD COLUMN IF NOT EXISTS lote_vd TEXT")
            cur.execute("ALTER TABLE public.pu_otimizadas ADD COLUMN IF NOT EXISTS lote_pu TEXT")
        except:
            pass
            
        conn.commit()
        print("DEBUG: Tabela criada/verificada")
        
        total_inseridas = 0
        
        print("DEBUG: Iniciando inserções")
        for i, peca in enumerate(pecas_selecionadas):
            print(f"DEBUG: Inserindo peça {i+1}: {peca}")
            
            # Buscar camadas da peça na tabela pu_camadas
            cur.execute("""
                SELECT l1, l3, l3_b FROM public.pu_camadas
                WHERE projeto = %s AND peca = %s
            """, (peca.get('projeto', ''), peca.get('peca', '')))
            
            camadas_result = cur.fetchone()
            camadas_para_inserir = []
            
            if camadas_result:
                l1_value = camadas_result[0]
                l3_value = camadas_result[1]
                l3_b_value = camadas_result[2] if len(camadas_result) > 2 else None
                
                # Verificar L1
                if l1_value and l1_value != '-' and str(l1_value).strip():
                    try:
                        qtd_l1 = int(l1_value)
                        for _ in range(qtd_l1):
                            camadas_para_inserir.append('L1')
                    except:
                        camadas_para_inserir.append('L1')
                
                # Verificar L3
                if l3_value and l3_value != '-' and str(l3_value).strip():
                    try:
                        qtd_l3 = int(l3_value)
                        for _ in range(qtd_l3):
                            camadas_para_inserir.append('L3')
                    except:
                        camadas_para_inserir.append('L3')
                
                # Verificar L3_B
                if l3_b_value and l3_b_value != '-' and str(l3_b_value).strip():
                    try:
                        qtd_l3_b = int(l3_b_value)
                        for _ in range(qtd_l3_b):
                            camadas_para_inserir.append('L3_B')
                    except:
                        camadas_para_inserir.append('L3_B')
            
            # Se não encontrou camadas, inserir sem camada
            if not camadas_para_inserir:
                camadas_para_inserir = [None]
            
            # Buscar lote da peça na tabela plano_controle_corte_vidro2
            cur.execute("""
                SELECT id_lote FROM public.plano_controle_corte_vidro2
                WHERE op = %s AND peca = %s
                LIMIT 1
            """, (peca.get('op', ''), peca.get('peca', '')))
            lote_result = cur.fetchone()
            if lote_result and lote_result[0]:
                lote_vd = lote_result[0]
                lote_pu = 'PU' + lote_vd[2:] if len(lote_vd) >= 3 else lote_vd
            else:
                lote_vd = ''
                lote_pu = ''
            
            # Inserir uma linha para cada camada
            for camada in camadas_para_inserir:
                # Converter L3_B para L3 no banco (manter compatibilidade)
                camada_db = 'L3' if camada == 'L3_B' else camada
                
                cur.execute("""
                    INSERT INTO public.pu_otimizadas (op_pai, op, peca, projeto, veiculo, local, rack, user_otimizacao, tipo, camada, lote_vd, lote_pu)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'PU', %s, %s, %s)
                """, (
                    peca.get('op_pai', ''),
                    peca.get('op', ''),
                    peca.get('peca', ''),
                    peca.get('projeto', ''),
                    peca.get('veiculo', ''),
                    peca.get('local', ''),
                    peca.get('rack', ''),
                    current_user.username,
                    camada_db,
                    lote_vd,
                    lote_pu
                ))
                
                # Inserir também na tabela pu_corte
                cur.execute("""
                    INSERT INTO public.pu_corte (op, peca, projeto, veiculo, user_otimizacao, tipo, camada)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    peca.get('op', ''),
                    peca.get('peca', ''),
                    peca.get('projeto', ''),
                    peca.get('veiculo', ''),
                    current_user.username,
                    'PU',
                    camada_db
                ))
                
                total_inseridas += 1
            
            print(f"DEBUG: Peça {i+1} inserida com {len(camadas_para_inserir)} camada(s)")
        
        print("DEBUG: Fazendo commit")
        conn.commit()
        
        # Atualizar status para PROGRAMADO na tabela plano_controle_corte_vidro2 apenas para as peças otimizadas
        ops_processadas = set()
        for peca in pecas_selecionadas:
            op = peca.get('op', '')
            peca_codigo = peca.get('peca', '')
            if op and peca_codigo:
                chave_peca = f"{op}_{peca_codigo}"
                if chave_peca not in ops_processadas:
                    cur.execute("""
                        UPDATE public.plano_controle_corte_vidro2 
                        SET pu_cortado = 'PROGRAMADO'
                        WHERE op = %s AND peca = %s
                    """, (op, peca_codigo))
                    ops_processadas.add(chave_peca)
        
        # Limpar peças manuais após otimização
        cur.execute("DELETE FROM public.pu_manuais")
        conn.commit()
        
        conn.close()
        print("DEBUG: Sucesso!")
        
        return jsonify({
            'success': True, 
            'message': f'{len(pecas_selecionadas)} peça(s) processada(s), {total_inseridas} linha(s) inserida(s) na otimização!',
            'redirect': '/otimizadas'
        })
    
    except Exception as e:
        if conn:
            try:
                conn.close()
            except:
                pass
        import traceback
        error_msg = traceback.format_exc()
        print(f"ERRO na otimização: {error_msg}")
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'}), 500

@app.route('/api/otimizadas')
@login_required
def api_otimizadas():
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("""
            SELECT id, op_pai, op, peca, projeto, veiculo, local, rack, cortada, user_otimizacao, data_otimizacao, camada, sensor 
            FROM public.pu_otimizadas 
            WHERE tipo = 'PU'
            ORDER BY id DESC
        """)
        dados = cur.fetchall()
        conn.close()
        
        resultado = []
        for row in dados:
            item = dict(row)
            if item['data_otimizacao']:
                item['data_otimizacao'] = item['data_otimizacao'].isoformat()
            item['sensor'] = item.get('sensor') or ''
            resultado.append(item)
        
        return jsonify(resultado)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/excluir-otimizadas', methods=['POST'])
@login_required
def excluir_otimizadas():
    try:
        dados = request.get_json()
        ids = dados.get('ids', [])
        motivo = dados.get('motivo', '').strip()
        
        if not ids:
            return jsonify({'success': False, 'message': 'Nenhuma peça selecionada'})
        
        if not motivo:
            return jsonify({'success': False, 'message': 'Motivo da exclusão é obrigatório'})
        
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Buscar peças antes de excluir
        placeholders = ','.join(['%s'] * len(ids))
        cur.execute(f"""
            SELECT * FROM public.pu_otimizadas 
            WHERE id IN ({placeholders}) AND tipo = 'PU'
        """, ids)
        pecas = cur.fetchall()
        
        # Adicionar colunas lote_vd e lote_pu se não existirem na tabela pu_exit
        try:
            cur.execute("ALTER TABLE public.pu_exit ADD COLUMN IF NOT EXISTS lote_vd TEXT")
            cur.execute("ALTER TABLE public.pu_exit ADD COLUMN IF NOT EXISTS lote_pu TEXT")
        except:
            pass
        
        # Inserir na tabela pu_exit com motivo
        for peca in pecas:
            cur.execute("""
                INSERT INTO public.pu_exit (op_pai, op, peca, projeto, veiculo, local, rack, usuario, data, motivo, lote_vd, lote_pu)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                peca['op_pai'],
                peca['op'],
                peca['peca'],
                peca['projeto'],
                peca['veiculo'],
                peca['local'],
                peca['rack'],
                current_user.username,
                datetime.now(timezone(timedelta(hours=-3))),
                f'EXCLUSÃO: {motivo}',
                peca.get('lote_vd'),
                peca.get('lote_pu')
            ))
        
        # Remover das otimizadas
        cur.execute(f"DELETE FROM public.pu_otimizadas WHERE id IN ({placeholders})", ids)
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'{len(pecas)} peça(s) excluída(s) com sucesso!'
        })
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'}), 500

@app.route('/api/enviar-estoque', methods=['POST'])
@login_required
def enviar_estoque():
    conn = None
    try:
        dados = request.get_json()
        ids = dados.get('ids', [])
        
        if not ids:
            return jsonify({'success': False, 'message': 'Nenhuma peça selecionada'})
        
        # Processar em lotes menores para evitar timeout
        batch_size = 50
        total_processadas = 0
        
        for i in range(0, len(ids), batch_size):
            batch_ids = ids[i:i + batch_size]
            
            conn = get_db_connection()
            conn.autocommit = False
            
            try:
                cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
                
                # Buscar peças do lote atual
                placeholders = ','.join(['%s'] * len(batch_ids))
                cur.execute(f"""
                    SELECT * FROM public.pu_otimizadas 
                    WHERE id IN ({placeholders}) AND tipo = 'PU'
                """, batch_ids)
                pecas = cur.fetchall()
                
                if not pecas:
                    conn.close()
                    continue
                
                # Preparar dados para inserção em lote
                dados_estoque = []
                dados_controle = []
                lotes_para_atualizar = set()
                
                for peca in pecas:
                    dados_estoque.append((
                        peca['op_pai'], peca['op'], peca['peca'], peca['projeto'], 
                        peca['veiculo'], peca['local'], peca['rack'], 
                        current_user.username, peca.get('camada'), peca.get('lote_vd'), peca.get('lote_pu')
                    ))
                    
                    dados_controle.append((
                        peca['op_pai'], peca['op'], peca['peca'], peca['projeto'], 
                        peca['veiculo'], peca['local'], peca['rack'], True, 
                        current_user.username, 'PU', peca.get('camada')
                    ))
                    
                    # Coletar lotes para atualizar status
                    if peca.get('lote_vd'):
                        lotes_para_atualizar.add(peca.get('lote_vd'))
                
                # Adicionar colunas lote_vd e lote_pu se não existirem
                try:
                    cur.execute("ALTER TABLE public.pu_inventory ADD COLUMN IF NOT EXISTS lote_vd TEXT")
                    cur.execute("ALTER TABLE public.pu_inventory ADD COLUMN IF NOT EXISTS lote_pu TEXT")
                except:
                    pass
                
                # Inserção em lote no estoque
                cur.executemany("""
                    INSERT INTO public.pu_inventory (op_pai, op, peca, projeto, veiculo, local, rack, data, usuario, camada, lote_vd, lote_pu)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, %s, %s, %s, %s)
                """, dados_estoque)
                
                # Verificar e atualizar status dos lotes
                for lote in lotes_para_atualizar:
                    lote_pu = 'PU' + lote[2:] if len(lote) >= 2 else lote
                    verificar_e_atualizar_status_lote(lote, lote_pu, cur)
                
                # Inserção em lote no controle
                cur.executemany("""
                    INSERT INTO public.pu_controle (op_pai, op, peca, projeto, veiculo, local, rack, cortada, user_otimizacao, tipo, camada)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, dados_controle)
                
                # Remover da tabela de otimizadas em lote
                cur.execute(f"DELETE FROM public.pu_otimizadas WHERE id IN ({placeholders})", batch_ids)
                
                conn.commit()
                total_processadas += len(pecas)
                
            except Exception as batch_error:
                conn.rollback()
                raise batch_error
            finally:
                conn.close()
        
        # Log da ação final
        if total_processadas > 0:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO public.pu_logs (usuario, acao, detalhes, data_acao)
                VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
            """, (
                current_user.username,
                'ENVIAR_ESTOQUE',
                f'Enviou {total_processadas} peça(s) para o estoque'
            ))
            conn.commit()
            conn.close()
        
        return jsonify({
            'success': True,
            'message': f'{total_processadas} peça(s) enviada(s) para o estoque com sucesso!'
        })
    
    except Exception as e:
        if conn:
            try:
                conn.rollback()
                conn.close()
            except:
                pass
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'}), 500

@app.route('/api/remover-estoque', methods=['POST'])
@login_required
def remover_estoque():
    conn = None
    try:
        dados = request.get_json()
        ids = dados.get('ids', [])
        tipo_operacao = dados.get('tipo_operacao', 'saida_individual')
        
        if not ids:
            return jsonify({'success': False, 'message': 'Nenhuma peça selecionada'})
        
        # Determinar o motivo baseado no tipo de operação
        if tipo_operacao == 'saida_massiva' and len(ids) > 1:
            motivo = 'SAÍDA MASSIVA'
            acao_log = 'SAIDA_MASSIVA'
            detalhes_log = f'Realizou saída massiva de {len(ids)} peça(s) do estoque'
        else:
            motivo = 'SAÍDA DO ESTOQUE'
            acao_log = 'SAIDA_ESTOQUE'
            detalhes_log = f'Removeu {len(ids)} peça(s) do estoque'
        
        # Processar em lotes menores para evitar timeout
        batch_size = 50
        total_removidas = 0
        
        for i in range(0, len(ids), batch_size):
            batch_ids = ids[i:i + batch_size]
            
            conn = get_db_connection()
            conn.autocommit = False
            
            try:
                cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
                
                # Buscar peças do lote atual
                placeholders = ','.join(['%s'] * len(batch_ids))
                cur.execute(f"SELECT * FROM public.pu_inventory WHERE id IN ({placeholders})", batch_ids)
                pecas = cur.fetchall()
                
                if not pecas:
                    conn.close()
                    continue
                
                # Adicionar colunas lote_vd e lote_pu se não existirem na tabela pu_exit
                try:
                    cur.execute("ALTER TABLE public.pu_exit ADD COLUMN IF NOT EXISTS lote_vd TEXT")
                    cur.execute("ALTER TABLE public.pu_exit ADD COLUMN IF NOT EXISTS lote_pu TEXT")
                except:
                    pass
                
                # Preparar dados para inserção em lote no pu_exit
                dados_exit = []
                for peca in pecas:
                    dados_exit.append((
                        peca.get('op_pai', ''), peca['op'], peca['peca'], 
                        peca.get('projeto', ''), peca.get('veiculo', ''), 
                        peca['local'], peca.get('rack', ''), 
                        current_user.username, motivo, peca.get('lote_vd'), peca.get('lote_pu')
                    ))
                
                # Inserção em lote no pu_exit
                cur.executemany("""
                    INSERT INTO public.pu_exit (op_pai, op, peca, projeto, veiculo, local, rack, usuario, data, motivo, lote_vd, lote_pu)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, %s, %s, %s)
                """, dados_exit)
                
                # Remover do estoque em lote
                cur.execute(f"DELETE FROM public.pu_inventory WHERE id IN ({placeholders})", batch_ids)
                
                conn.commit()
                total_removidas += len(pecas)
                
            except Exception as batch_error:
                conn.rollback()
                raise batch_error
            finally:
                conn.close()
        
        # Log da ação final
        if total_removidas > 0:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO public.pu_logs (usuario, acao, detalhes, data_acao)
                VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
            """, (current_user.username, acao_log, f'Removeu {total_removidas} peça(s) do estoque'))
            conn.commit()
            conn.close()
        
        return jsonify({'success': True, 'message': f'{total_removidas} peça(s) removida(s) do estoque!'})
    
    except Exception as e:
        if conn:
            try:
                conn.rollback()
                conn.close()
            except:
                pass
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'}), 500

@app.route('/api/arquivos')
@login_required
def api_arquivos():
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Resetar sequência do ID para evitar duplicatas
        try:
            cur.execute("SELECT setval('arquivos_pu_id_seq', (SELECT COALESCE(MAX(id), 0) + 1 FROM public.arquivos_pu), false)")
            conn.commit()
        except:
            pass
        
        # Buscar dados
        cur.execute("SELECT * FROM public.arquivos_pu ORDER BY id DESC")
        dados = cur.fetchall()
        conn.close()
        
        return jsonify([dict(row) for row in dados])
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/arquivos', methods=['POST', 'OPTIONS'])
@login_required
def adicionar_arquivo():
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        return response
        
    try:
        # Tentar diferentes formas de obter os dados
        dados = None
        if request.is_json:
            dados = request.get_json()
        else:
            dados = request.get_json(force=True)
            
        if not dados:
            response = jsonify({'success': False, 'message': 'Dados não recebidos'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response
        
        projeto = dados.get('projeto', '').strip()
        peca = dados.get('peca', '').strip()
        nome_peca = dados.get('nome_peca', '').strip()
        camada = dados.get('camada', '').strip()
        espessura = dados.get('espessura')
        quantidade = dados.get('quantidade')
        sensor = dados.get('sensor', '').strip()
        
        if not all([projeto, peca, nome_peca, camada]):
            response = jsonify({'success': False, 'message': 'Projeto, peça, nome da peça e camada são obrigatórios'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response
        
        # Converter valores numéricos
        try:
            espessura_val = float(espessura) if espessura else 0.5
        except:
            espessura_val = 0.5
            
        try:
            quantidade_val = int(quantidade) if quantidade else 1
        except:
            quantidade_val = 1
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO public.arquivos_pu (projeto, peca, nome_peca, camada, espessura, quantidade, sensor)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (projeto, peca, nome_peca, camada, espessura_val, quantidade_val, sensor))
        
        conn.commit()
        conn.close()
        
        response = jsonify({'success': True, 'message': 'Arquivo adicionado com sucesso!'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
        
    except Exception as e:
        response = jsonify({'success': False, 'message': f'Erro: {str(e)}'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@app.route('/api/arquivos/<int:arquivo_id>', methods=['PUT', 'OPTIONS'])
@login_required
def editar_arquivo(arquivo_id):
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'PUT')
        return response
        
    try:
        dados = request.get_json(force=True)
        projeto = dados.get('projeto', '').strip()
        peca = dados.get('peca', '').strip()
        nome_peca = dados.get('nome_peca', '').strip()
        camada = dados.get('camada', '').strip()
        espessura = dados.get('espessura') or 0.5
        quantidade = dados.get('quantidade') or 1
        sensor = dados.get('sensor', '').strip()
        
        if not all([projeto, peca, nome_peca, camada]):
            response = jsonify({'success': False, 'message': 'Projeto, peça, nome da peça e camada são obrigatórios'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            UPDATE public.arquivos_pu 
            SET projeto = %s, peca = %s, nome_peca = %s, camada = %s, 
                espessura = %s, quantidade = %s, sensor = %s
            WHERE id = %s
        """, (projeto, peca, nome_peca, camada, float(espessura), int(quantidade), sensor, arquivo_id))
        
        conn.commit()
        conn.close()
        
        response = jsonify({'success': True, 'message': 'Arquivo atualizado com sucesso!'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
        
    except Exception as e:
        response = jsonify({'success': False, 'message': f'Erro: {str(e)}'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@app.route('/api/arquivos/<int:arquivo_id>', methods=['DELETE', 'OPTIONS'])
@login_required
def excluir_arquivo(arquivo_id):
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'DELETE')
        return response
        
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("DELETE FROM public.arquivos_pu WHERE id = %s", (arquivo_id,))
        
        conn.commit()
        conn.close()
        
        response = jsonify({'success': True, 'message': 'Arquivo excluído com sucesso!'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
        
    except Exception as e:
        response = jsonify({'success': False, 'message': f'Erro: {str(e)}'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@app.route('/api/locais')
def api_locais():
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("SELECT id, local, rack, nome, status FROM public.pu_locais ORDER BY id")
        dados = cur.fetchall()
        conn.close()
        return jsonify([dict(row) for row in dados])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/contagem-pecas-locais')
@login_required
def api_contagem_pecas_locais():
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        cur.execute("""
            SELECT local, COUNT(*) as total 
            FROM (
                SELECT local FROM public.pu_inventory WHERE local IS NOT NULL AND local != ''
                UNION ALL
                SELECT local FROM public.pu_otimizadas WHERE tipo = 'PU' AND local IS NOT NULL AND local != ''
            ) AS combined
            GROUP BY local
        """)
        dados = [dict(row) for row in cur.fetchall()]
        
        conn.close()
        return jsonify(dados)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/local-detalhes/<local>')
@login_required
def api_local_detalhes(local):
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        cur.execute("""
            SELECT op, peca, projeto, veiculo FROM public.pu_inventory WHERE local = %s
            UNION ALL
            SELECT op, peca, projeto, veiculo FROM public.pu_otimizadas WHERE local = %s AND tipo = 'PU'
        """, (local, local))
        pecas = [dict(row) for row in cur.fetchall()]
        
        conn.close()
        
        return jsonify({
            'local': local,
            'pecas': pecas,
            'total': len(pecas)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Executar uma única vez para popular a tabela
def popular_locais_iniciais():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Verificar se tabela pu_locais existe
        cur.execute("SELECT COUNT(*) FROM public.pu_locais LIMIT 1")
        print("Tabela pu_locais já existe")
        
        conn.close()
        
    except Exception as e:
        print(f"Tabela não existe, criando: {e}")
        # Se deu erro, criar tabelas básicas
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            
            cur.execute("""
                CREATE TABLE IF NOT EXISTS public.pu_locais (
                    id SERIAL PRIMARY KEY,
                    local TEXT,
                    rack TEXT,
                    status TEXT DEFAULT 'Ativo',
                    nome TEXT
                )
            """)
            
            conn.commit()
            conn.close()
            print("Tabela pu_locais criada")
        except Exception as e2:
            print(f"Erro ao criar tabela: {e2}")

# Executar automaticamente na inicialização
try:
    print("Verificando tabelas...")
    popular_locais_iniciais()
    print("Verificação concluída!")
except Exception as e:
    print(f"Aviso na inicialização: {e}")
    print("Continuando mesmo assim...")

@app.route('/api/adicionar-local', methods=['POST'])
@login_required
def adicionar_local():
    try:
        data = request.get_json()
        local = data.get('local')
        nome = data.get('nome')

        if not local or not nome:
            return jsonify({'success': False, 'message': 'Preencha todos os campos.'})

        conn = get_db_connection()
        cur = conn.cursor()
        
        # Verificar se local já existe
        cur.execute("SELECT id FROM public.pu_locais WHERE local = %s", (local,))
        if cur.fetchone():
            conn.close()
            return jsonify({'success': False, 'message': 'Local já existe'})

        cur.execute("""
            INSERT INTO public.pu_locais (local, rack, status, nome)
            VALUES (%s, %s, %s, %s)
        """, (local, 'COLMEIA', 'Ativo', nome))

        conn.commit()
        conn.close()

        return jsonify({'success': True, 'message': 'Local adicionado com sucesso!'})

    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro ao adicionar local: {str(e)}'})

@app.route('/api/alterar-status-local', methods=['PUT'])
@login_required
def alterar_status_local():
    try:
        data = request.get_json()
        local = data.get('local')
        status = data.get('status')

        if not local or not status:
            return jsonify({'success': False, 'message': 'Dados incompletos'})

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            UPDATE public.pu_locais 
            SET status = %s 
            WHERE local = %s
        """, (status, local))

        if cur.rowcount == 0:
            conn.close()
            return jsonify({'success': False, 'message': 'Local não encontrado'})

        conn.commit()
        conn.close()

        return jsonify({'success': True, 'message': f'Status alterado para {status}!'})

    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro ao alterar status: {str(e)}'})



@app.route('/api/saidas')
def api_saidas():
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Verificar se tabela existe
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'pu_exit'
            )
        """)
        tabela_existe = cur.fetchone()[0]
        
        if not tabela_existe:
            conn.close()
            return jsonify({'dados': [], 'pagination': {'current_page': 1, 'total_pages': 1, 'total_records': 0, 'limit': 50}})
        
        cur.execute("SELECT id, op, peca, local, usuario, data FROM public.pu_exit ORDER BY id DESC LIMIT 50")
        dados = cur.fetchall()
        conn.close()
        
        resultado = []
        for row in dados:
            item = dict(row)
            if item.get('data'):
                item['data'] = item['data'].strftime('%d/%m/%Y')
            resultado.append(item)
        
        return jsonify({
            'dados': resultado,
            'pagination': {'current_page': 1, 'total_pages': 1, 'total_records': len(resultado), 'limit': 50}
        })
    except Exception as e:
        print(f"Erro na API saidas: {e}")
        return jsonify({'dados': [], 'pagination': {'current_page': 1, 'total_pages': 1, 'total_records': 0, 'limit': 50}})

@app.route('/api/saidas-exit')
@login_required
def api_saidas_exit():
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("SELECT op_pai, op, peca, projeto, veiculo, local, rack, usuario, data, motivo FROM public.pu_exit ORDER BY id DESC")
        dados = cur.fetchall()
        conn.close()
        
        resultado = []
        for row in dados:
            item = dict(row)
            if item.get('data'):
                item['data'] = item['data'].strftime('%d/%m/%Y')
            resultado.append(item)
        
        return jsonify(resultado)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/gerar-xml', methods=['POST'])
@login_required
def gerar_xml():
    try:
        if request.is_json:
            dados = request.get_json()
            pecas_selecionadas = dados.get('pecas', [])
        else:
            pecas_json = request.form.get('pecas', '[]')
            pecas_selecionadas = json.loads(pecas_json)
        
        if not pecas_selecionadas:
            return jsonify({'success': False, 'message': 'Nenhuma peça selecionada'})
        
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        import zipfile
        import os
        from xml.etree.ElementTree import Element, SubElement, tostring
        from xml.dom import minidom
        
        zip_buffer = io.BytesIO()
        xmls_gerados = []
        xmls_nao_gerados = []
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for peca_data in pecas_selecionadas:
                projeto = peca_data.get('projeto', '')
                peca_codigo = peca_data['peca']
                op = peca_data['op']
                
                # Buscar camadas da peça na tabela pu_camadas
                cur.execute("""
                    SELECT l1, l3, l3_b FROM public.pu_camadas
                    WHERE projeto = %s AND peca = %s
                """, (projeto, peca_codigo))
                
                camadas_result = cur.fetchone()
                camadas_para_gerar = []
                
                if camadas_result:
                    l1_value = camadas_result['l1']
                    l3_value = camadas_result['l3']
                    l3_b_value = camadas_result.get('l3_b')
                    
                    # Verificar L1
                    if l1_value and l1_value != '-' and str(l1_value).strip():
                        try:
                            qtd_l1 = int(l1_value)
                            for _ in range(qtd_l1):
                                camadas_para_gerar.append('L1')
                        except:
                            camadas_para_gerar.append('L1')
                    
                    # Verificar L3
                    if l3_value and l3_value != '-' and str(l3_value).strip():
                        try:
                            qtd_l3 = int(l3_value)
                            for _ in range(qtd_l3):
                                camadas_para_gerar.append('L3')
                        except:
                            camadas_para_gerar.append('L3')
                    
                    # Verificar L3_B
                    if l3_b_value and l3_b_value != '-' and str(l3_b_value).strip():
                        try:
                            qtd_l3_b = int(l3_b_value)
                            for _ in range(qtd_l3_b):
                                camadas_para_gerar.append('L3_B')
                        except:
                            camadas_para_gerar.append('L3_B')
                
                # Se não encontrou camadas, não gerar XML
                if not camadas_para_gerar:
                    xmls_nao_gerados.append(f"{projeto} {peca_codigo} - Sem camadas definidas")
                    continue
                
                # Gerar XMLs baseado nas camadas encontradas
                xml_count = 0
                camada_count = {}  # Contador por tipo de camada
                
                for camada in camadas_para_gerar:
                    # Determinar sufixo do arquivo baseado na camada
                    if camada == 'L3_B':
                        sufixo_arquivo = '-B'
                        camada_xml = 'L3'
                    else:
                        sufixo_arquivo = '-A'
                        camada_xml = camada
                    
                    # Contar camadas por tipo para numeração única
                    if camada_xml not in camada_count:
                        camada_count[camada_xml] = 0
                    camada_count[camada_xml] += 1
                    
                    # Buscar arquivo correspondente à camada com sufixo
                    cur.execute("""
                        SELECT * FROM public.arquivos_pu
                        WHERE projeto = %s AND peca = %s AND camada = %s AND nome_peca LIKE %s
                        LIMIT 1
                    """, (projeto, peca_codigo, camada_xml, f'%{sufixo_arquivo}'))
                    
                    arquivo_info = cur.fetchone()
                    
                    if not arquivo_info:
                        # Se não encontrou com sufixo, buscar genérico da camada
                        cur.execute("""
                            SELECT * FROM public.arquivos_pu
                            WHERE projeto = %s AND peca = %s AND camada = %s
                            LIMIT 1
                        """, (projeto, peca_codigo, camada_xml))
                        arquivo_info = cur.fetchone()
                    
                    if arquivo_info:
                        # Usar campos disponíveis ou valores padrão
                        nome_peca = arquivo_info.get('nome_peca', arquivo_info.get('caminho', peca_codigo))
                        espessura = arquivo_info.get('espessura', '1.0')
                        
                        # Criar XML
                        root = Element('RPOrderGenerator')
                        root.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
                        root.set('xmlns:xsd', 'http://www.w3.org/2001/XMLSchema')

                        queued_item = SubElement(root, 'QueuedItem')

                        SubElement(queued_item, 'Driver').text = 'D006'
                        SubElement(queued_item, 'TransactionId').text = '000'
                        SubElement(queued_item, 'PartCode').text = nome_peca

                        # Adicionar os campos solicitados
                        SubElement(queued_item, 'CustomerCode').text = peca_data.get('veiculo', '')  # Nome do veículo
                        part_description = f"{peca_data.get('local', '')} | {projeto} | {peca_codigo} | {camada_xml}"
                        SubElement(queued_item, 'CustomerDescription').text = part_description  # Concatenação como antes

                        SubElement(queued_item, 'Material').text = 'Acrílico-0'
                        SubElement(queued_item, 'Thickness').text = str(espessura)
                        
                        # Incrementar contador geral
                        xml_count += 1
                        
                        # Gerar Order único: OP + letra sequencial geral
                        letra_sequencia = chr(ord('A') + xml_count - 1)
                        SubElement(queued_item, 'Order').text = f"{peca_data['op']}-{letra_sequencia}"
                        SubElement(queued_item, 'QtyRequired').text = '1'  # Sempre 1 por XML
                        SubElement(queued_item, 'DeliveryDate').text = datetime.now().strftime('%d/%m/%Y')
                        SubElement(queued_item, 'FilePart').text = nome_peca

                        # Formatar XML
                        rough_string = tostring(root, 'utf-8')
                        reparsed = minidom.parseString(rough_string)
                        pretty_xml = reparsed.toprettyxml(indent='  ', encoding='utf-8')
                        
                        # Nome único do arquivo XML: OP_PECA_PROJETO_CAMADA_SUFIXO_NUMERO
                        xml_filename = f"{op}_{peca_codigo}_{projeto}_{camada_xml}{sufixo_arquivo}_{camada_count[camada_xml]:02d}.xml"
                        zip_file.writestr(xml_filename, pretty_xml)
                    else:
                        # Se não encontrou arquivo, adicionar aos não gerados
                        xmls_nao_gerados.append(f"{projeto} {peca_codigo} {camada_xml}{sufixo_arquivo} - Arquivo não encontrado")
                
                if xml_count > 0:
                    xmls_gerados.append(f"OP {op} - Peça {peca_codigo} - {xml_count} XML(s) gerado(s) ({len(camadas_para_gerar)} camada(s))")
                else:
                    xmls_nao_gerados.append(f"{projeto} {peca_codigo} - Nenhum arquivo encontrado para as camadas")
        
        # Contar total de XMLs gerados
        total_xmls_gerados = sum(int(msg.split(' - ')[2].split(' ')[0]) for msg in xmls_gerados if ' - ' in msg)
        
        # Log da ação com detalhes
        if xmls_nao_gerados:
            detalhes_log = f"XMLs: {total_xmls_gerados} gerados, {len(xmls_nao_gerados)} problemas - {'; '.join(xmls_nao_gerados[:3])}"
            if len(xmls_nao_gerados) > 3:
                detalhes_log += f" e mais {len(xmls_nao_gerados) - 3}"
        else:
            detalhes_log = f"Gerou {total_xmls_gerados} XML(s) com sucesso para {len(xmls_gerados)} peça(s)"
        
        cur.execute("""
            INSERT INTO public.pu_logs (usuario, acao, detalhes)
            VALUES (%s, %s, %s)
        """, (current_user.username, 'GERAR_XML', detalhes_log))
        
        conn.commit()
        conn.close()
        
        # Se não gerou nenhum XML
        if not xmls_gerados:
            return jsonify({
                'success': False, 
                'message': f'Nenhum XML foi gerado.\n\nProblemas encontrados:\n• {"; ".join(xmls_nao_gerados[:10])}'
            })
        
        zip_buffer.seek(0)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Preparar mensagem de retorno
        total_xmls_gerados = sum(int(msg.split(' - ')[2].split(' ')[0]) for msg in xmls_gerados if ' - ' in msg)
        mensagem = f'{len(xmls_gerados)} peça(s) processada(s), {total_xmls_gerados} XML(s) gerado(s) com sucesso!'
        if xmls_nao_gerados:
            mensagem += f'\n\nProblemas encontrados ({len(xmls_nao_gerados)}):'
            for item in xmls_nao_gerados[:5]:  # Mostrar apenas os primeiros 5
                mensagem += f'\n• {item}'
            if len(xmls_nao_gerados) > 5:
                mensagem += f'\n• ... e mais {len(xmls_nao_gerados) - 5} problema(s)'
        
        # Tentar salvar ZIP na pasta do SharePoint
        zip_saved_sharepoint = False
        sharepoint_paths = [
            os.path.expanduser(r"~\CARBON CARS\Programação e Controle de Produção - DocumentosPCP\AUTOMACAO LIBELLULA"),
            os.path.expanduser(r"~\OneDrive - CARBON CARS\Programação e Controle de Produção - DocumentosPCP\AUTOMACAO LIBELLULA"),
            os.path.expanduser(r"~\OneDrive\CARBON CARS\Programação e Controle de Produção - DocumentosPCP\AUTOMACAO LIBELLULA"),
            os.path.expanduser(r"~\Documents\XMLs"),
            os.path.expanduser(r"~\Downloads")
        ]
        
        zip_filename = f'xmls_otimizacao_{timestamp}.zip'
        
        for sharepoint_path in sharepoint_paths:
            try:
                # Criar diretório se não existir
                os.makedirs(sharepoint_path, exist_ok=True)
                
                if os.path.exists(sharepoint_path) and os.access(sharepoint_path, os.W_OK):
                    zip_file_path = os.path.join(sharepoint_path, zip_filename)
                    with open(zip_file_path, 'wb') as f:
                        f.write(zip_buffer.getvalue())
                    zip_saved_sharepoint = True
                    mensagem += f"\n\nArquivo ZIP salvo em: {sharepoint_path}"
                    break
            except Exception as e:
                print(f"Erro ao salvar em {sharepoint_path}: {e}")
                continue
        
        if not zip_saved_sharepoint:
            mensagem += "\n\nAVISO: Não foi possível salvar em pasta sincronizada. Arquivo disponível apenas para download."
        
        # Sempre retornar o arquivo para download
        zip_buffer.seek(0)
        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name=zip_filename
        )
    except Exception as e:
        import traceback
        print("Erro ao gerar XML:", traceback.format_exc())  # Log detalhado no console
        return jsonify({'success': False, 'message': f'Erro ao gerar XMLs: {str(e)}'}), 500

@app.route('/download-xml/<filename>')
@login_required
def download_xml(filename):
    import tempfile
    import os
    
    temp_dir = tempfile.gettempdir()
    file_path = os.path.join(temp_dir, filename)
    
    if os.path.exists(file_path):
        def remove_file(response):
            try:
                os.remove(file_path)
            except:
                pass
            return response
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return send_file(file_path, as_attachment=True, download_name=f'xmls_otimizacao_{timestamp}.zip')
    else:
        return jsonify({'error': 'Arquivo não encontrado'}), 404

@app.route('/api/gerar-excel-otimizacao', methods=['POST'])
@login_required
def gerar_excel_otimizacao():
    try:
        dados_json = request.form.get('dados', '[]')
        dados = json.loads(dados_json)
        
        if not dados:
            return jsonify({'success': False, 'message': 'Nenhum dado encontrado'})
        
        df = pd.DataFrame(dados)
        df = df.rename(columns={
            'op_pai': 'OP-PAI',
            'op': 'OP',
            'peca': 'PEÇA',
            'projeto': 'PROJETO',
            'veiculo': 'VEÍCULO',
            'local': 'LOCAL',
            'rack': 'RACK'
        })
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'otimizacao_{timestamp}.xlsx'
        
        output = io.BytesIO()
        df.to_excel(output, index=False, engine='openpyxl')
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro ao gerar Excel: {str(e)}'}), 500

@app.route('/api/gerar-excel-estoque', methods=['POST'])
def gerar_excel_estoque():
    try:
        dados_json = request.form.get('dados', '[]')
        dados = json.loads(dados_json)
        
        if not dados:
            return jsonify({'success': False, 'message': 'Nenhum dado encontrado'})
        
        df = pd.DataFrame(dados)
        df = df.rename(columns={
            'op': 'OP',
            'peca': 'PEÇA',
            'projeto': 'PROJETO',
            'veiculo': 'VEÍCULO',
            'local': 'LOCAL',
            'camada': 'CAMADA',
            'sensor': 'SENSOR',
            'data': 'DATA ENTRADA'
        })
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'estoque_{timestamp}.xlsx'
        
        output = io.BytesIO()
        df.to_excel(output, index=False, engine='openpyxl')
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro ao gerar Excel: {str(e)}'}), 500

@app.route('/api/gerar-excel-saidas', methods=['POST'])
@login_required
def gerar_excel_saidas():
    try:
        dados_json = request.form.get('dados', '[]')
        dados = json.loads(dados_json)
        
        if not dados:
            return jsonify({'success': False, 'message': 'Nenhum dado encontrado'})
        
        df = pd.DataFrame(dados)
        df = df.rename(columns={
            'op_pai': 'OP-PAI',
            'op': 'OP',
            'peca': 'PEÇA',
            'projeto': 'PROJETO',
            'veiculo': 'VEÍCULO',
            'local': 'LOCAL',
            'rack': 'RACK',
            'usuario': 'USUÁRIO',
            'data': 'DATA SAÍDA',
            'motivo': 'MOTIVO'
        })
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'saidas_{timestamp}.xlsx'
        
        output = io.BytesIO()
        df.to_excel(output, index=False, engine='openpyxl')
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro ao gerar Excel: {str(e)}'}), 500

@app.route('/api/gerar-excel-logs', methods=['POST'])
@login_required
def gerar_excel_logs():
    if current_user.setor != 'T.I' or current_user.role != 'admin':
        return jsonify({'success': False, 'message': 'Acesso negado'}), 403
    
    try:
        dados_json = request.form.get('dados', '[]')
        dados = json.loads(dados_json)
        
        if not dados:
            return jsonify({'success': False, 'message': 'Nenhum dado encontrado'})
        
        df = pd.DataFrame(dados)
        df = df.rename(columns={
            'usuario': 'USUÁRIO',
            'acao': 'AÇÃO',
            'detalhes': 'DETALHES',
            'data_acao': 'DATA AÇÃO'
        })
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'logs_{timestamp}.xlsx'
        
        output = io.BytesIO()
        df.to_excel(output, index=False, engine='openpyxl')
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro ao gerar Excel: {str(e)}'}), 500

@app.route('/api/gerar-excel-otimizadas', methods=['POST'])
@login_required
def gerar_excel_otimizadas():
    try:
        dados_json = request.form.get('dados', '[]')
        dados = json.loads(dados_json)
        
        if not dados:
            return jsonify({'success': False, 'message': 'Nenhum dado encontrado'})
        
        df = pd.DataFrame(dados)
        df = df.rename(columns={
            'op': 'OP',
            'peca': 'PEÇA',
            'projeto': 'PROJETO',
            'veiculo': 'VEÍCULO',
            'local': 'LOCAL',
            'camada': 'CAMADA',
            'sensor': 'SENSOR',
            'data': 'DATA OTIMIZAÇÃO',
            'status': 'STATUS'
        })
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'otimizadas_{timestamp}.xlsx'
        
        output = io.BytesIO()
        df.to_excel(output, index=False, engine='openpyxl')
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro ao gerar Excel: {str(e)}'}), 500

@app.route('/api/gerar-excel-locais', methods=['POST'])
@login_required
def gerar_excel_locais():
    try:
        dados_json = request.form.get('dados', '[]')
        dados = json.loads(dados_json)
        
        if not dados:
            return jsonify({'success': False, 'message': 'Nenhum dado encontrado'})
        
        df = pd.DataFrame(dados)
        df = df.rename(columns={
            'local': 'LOCAL',
            'nome': 'RACK',
            'status': 'STATUS',
            'quantidade_pecas': 'QUANTIDADE PEÇAS',
            'tem_pecas': 'TEM PEÇAS'
        })
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'locais_{timestamp}.xlsx'
        
        output = io.BytesIO()
        df.to_excel(output, index=False, engine='openpyxl')
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro ao gerar Excel: {str(e)}'}), 500

@app.route('/api/relatorio-controle')
@login_required
def api_relatorio_controle():
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Buscar contagem total e do dia atual por usuário
        cur.execute("""
            SELECT 
                user_otimizacao as usuario,
                COUNT(*) as total_enviado,
                COUNT(CASE WHEN DATE(data_otimizacao) = CURRENT_DATE THEN 1 END) as hoje
            FROM public.pu_controle 
            WHERE cortada = true
            GROUP BY user_otimizacao
            ORDER BY total_enviado DESC
        """)
        dados = cur.fetchall()
        conn.close()
        
        return jsonify([dict(row) for row in dados])
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/api/locais-disponiveis')
@login_required
def api_locais_disponiveis():
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Contar total de locais ativos
        cur.execute("SELECT COUNT(*) FROM public.pu_locais WHERE status = 'Ativo'")
        total_locais = cur.fetchone()[0]
        
        # Contar locais ocupados
        cur.execute("""
            SELECT COUNT(DISTINCT local) FROM (
                SELECT local FROM public.pu_inventory WHERE local IS NOT NULL AND local != ''
                UNION
                SELECT local FROM public.pu_otimizadas WHERE tipo = 'PU' AND local IS NOT NULL AND local != ''
                UNION
                SELECT local FROM public.pu_manuais WHERE local IS NOT NULL AND local != ''
            ) AS occupied
        """)
        locais_ocupados = cur.fetchone()[0]
        
        locais_disponiveis = total_locais - locais_ocupados
        
        conn.close()
        return jsonify({
            'total_locais': total_locais,
            'locais_ocupados': locais_ocupados,
            'locais_disponiveis': locais_disponiveis
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/buscar-op/<op>')
@login_required
def buscar_op(op):
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Buscar dados da OP na tabela dados_op do schema dados_uso_geral
        cur.execute("""
            SELECT codigo_veiculo, modelo 
            FROM dados_uso_geral.dados_op 
            WHERE op = %s and planta = 'Jarinu'
            LIMIT 1
        """, (op,))
        
        resultado = cur.fetchone()
        conn.close()
        
        if resultado:
            return jsonify({
                'success': True,
                'projeto': resultado['codigo_veiculo'] or '',
                'veiculo': resultado['modelo'] or ''
            })
        else:
            return jsonify({
                'success': False,
                'message': 'OP não encontrada'
            })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao buscar OP: {str(e)}'
        }), 500

@app.route('/api/upload-xlsx', methods=['POST'])
@login_required
def upload_xlsx():
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': 'Nenhum arquivo enviado'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'message': 'Nenhum arquivo selecionado'}), 400
        
        if not file.filename.lower().endswith('.xlsx'):
            return jsonify({'success': False, 'message': 'Apenas arquivos .xlsx são aceitos'}), 400
        
        # Ler arquivo Excel
        df = pd.read_excel(file, engine='openpyxl')
        
        if df.empty:
            return jsonify({'success': False, 'message': 'Arquivo vazio'}), 400
        
        # Verificar se tem as colunas obrigatórias (case insensitive)
        colunas_obrigatorias = ['op', 'peca', 'projeto', 'veiculo']
        colunas_arquivo = [col.lower().strip() for col in df.columns]
        
        # Mapear colunas do arquivo
        mapeamento_colunas = {}
        for col_obrig in colunas_obrigatorias:
            encontrada = False
            for i, col_arq in enumerate(colunas_arquivo):
                if col_obrig in col_arq or col_arq in col_obrig:
                    mapeamento_colunas[col_obrig] = df.columns[i]
                    encontrada = True
                    break
            if not encontrada:
                return jsonify({'success': False, 'message': f'Coluna "{col_obrig}" não encontrada no arquivo'}), 400
        
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Buscar locais ocupados
        cur.execute("""
            SELECT local FROM public.pu_inventory WHERE local IS NOT NULL AND local != '' 
            UNION 
            SELECT local FROM public.pu_otimizadas WHERE tipo = 'PU' AND local IS NOT NULL AND local != ''
            UNION
            SELECT local FROM public.pu_manuais WHERE local IS NOT NULL AND local != ''
        """)
        locais_ocupados = {row['local'] for row in cur.fetchall()}
        
        pecas_processadas = []
        pecas_com_erro = []
        locais_usados_nesta_sessao = set()
        
        for index, row in df.iterrows():
            try:
                # Função para limpar valores
                def limpar_valor(valor):
                    if pd.notna(valor):
                        valor_str = str(valor).strip()
                        # Remover .0 se for um número inteiro
                        if valor_str.endswith('.0') and valor_str.replace('.0', '').replace('-', '').isdigit():
                            valor_str = valor_str[:-2]
                        return valor_str
                    return ''
                
                # Usar mapeamento de colunas com limpeza
                op = limpar_valor(row[mapeamento_colunas['op']])
                peca = limpar_valor(row[mapeamento_colunas['peca']])
                projeto = limpar_valor(row[mapeamento_colunas['projeto']])
                veiculo = limpar_valor(row[mapeamento_colunas['veiculo']])
                
                # Sensor é opcional
                sensor = ''
                if 'sensor' in df.columns:
                    sensor = limpar_valor(row.get('sensor', ''))
                
                if not all([op, peca, projeto, veiculo]):
                    pecas_com_erro.append(f'Linha {index+2}: Campos obrigatórios em branco')
                    continue
                
                # Verificar se peça já existe
                cur.execute("""
                    SELECT COUNT(*) FROM (
                        SELECT 1 FROM public.pu_inventory WHERE op = %s AND peca = %s
                        UNION ALL
                        SELECT 1 FROM public.pu_otimizadas WHERE op = %s AND peca = %s AND tipo = 'PU'
                        UNION ALL
                        SELECT 1 FROM public.pu_manuais WHERE op = %s AND peca = %s
                    ) AS existing
                """, (op, peca, op, peca, op, peca))
                
                if cur.fetchone()[0] > 0:
                    pecas_com_erro.append(f'Linha {index+2}: Peça {peca} com OP {op} já existe')
                    continue
                
                # Combinar locais ocupados com os já usados nesta sessão
                locais_bloqueados = locais_ocupados | locais_usados_nesta_sessao
                
                # Buscar locais que já têm peças diferentes do tipo atual
                cur.execute("""
                    SELECT DISTINCT local FROM public.pu_inventory 
                    WHERE peca != %s AND local IS NOT NULL AND local != ''
                    UNION
                    SELECT DISTINCT local FROM public.pu_otimizadas 
                    WHERE peca != %s AND tipo = 'PU' AND local IS NOT NULL AND local != ''
                    UNION
                    SELECT DISTINCT local FROM public.pu_manuais 
                    WHERE peca != %s AND local IS NOT NULL AND local != ''
                """, (peca, peca, peca))
                locais_com_pecas_diferentes = {row['local'] for row in cur.fetchall()}
                
                # Combinar todos os locais bloqueados
                locais_bloqueados = locais_bloqueados | locais_com_pecas_diferentes
                
                # Sugerir local
                local_sugerido, rack_sugerido = sugerir_local_armazenamento(peca, locais_bloqueados, conn)
                
                if not local_sugerido or not rack_sugerido:
                    pecas_com_erro.append(f'Linha {index+2}: Não há locais disponíveis para peça {peca}')
                    continue
                
                # Buscar arquivo baseado no projeto, peça e sensor
                arquivo_status = "Sem arquivo"
                if peca == 'PBS' and sensor:
                    cur.execute("""
                        SELECT nome_peca FROM public.arquivos_pu
                        WHERE projeto = %s AND peca = %s AND sensor = %s
                        LIMIT 1
                    """, (projeto, peca, sensor))
                    arquivo_result = cur.fetchone()
                    if arquivo_result:
                        arquivo_status = arquivo_result['nome_peca']
                else:
                    cur.execute("""
                        SELECT nome_peca FROM public.arquivos_pu
                        WHERE projeto = %s AND peca = %s
                        LIMIT 1
                    """, (projeto, peca))
                    arquivo_result = cur.fetchone()
                    if arquivo_result:
                        arquivo_status = arquivo_result['nome_peca']
                
                # Inserir na tabela pu_manuais
                cur.execute("""
                    INSERT INTO public.pu_manuais (op, peca, projeto, veiculo, local, rack, arquivo, usuario)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (op, peca, projeto, veiculo, local_sugerido, rack_sugerido, arquivo_status, current_user.username))
                
                # Adicionar aos processados
                pecas_processadas.append({
                    'op': op,
                    'peca': peca,
                    'projeto': projeto,
                    'veiculo': veiculo,
                    'local': local_sugerido,
                    'rack': rack_sugerido,
                    'sensor': sensor,
                    'arquivo_status': arquivo_status
                })
                
                # Marcar local como usado
                locais_usados_nesta_sessao.add(local_sugerido)
                
            except Exception as row_error:
                pecas_com_erro.append(f'Linha {index+2}: Erro - {str(row_error)}')
                continue
        
        # Log da ação
        cur.execute("""
            INSERT INTO public.pu_logs (usuario, acao, detalhes, data_acao)
            VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
        """, (
            current_user.username,
            'UPLOAD_XLSX',
            f'Upload de arquivo XLSX: {len(pecas_processadas)} peças processadas, {len(pecas_com_erro)} com erro'
        ))
        
        conn.commit()
        conn.close()
        
        # Preparar resposta
        mensagem = f'{len(pecas_processadas)} peça(s) processada(s) com sucesso!'
        if pecas_com_erro:
            mensagem += f'\n\n{len(pecas_com_erro)} erro(s) encontrado(s):'
            for erro in pecas_com_erro[:5]:  # Mostrar apenas os primeiros 5 erros
                mensagem += f'\n• {erro}'
            if len(pecas_com_erro) > 5:
                mensagem += f'\n• ... e mais {len(pecas_com_erro) - 5} erro(s)'
        
        return jsonify({
            'success': True,
            'message': mensagem,
            'processadas': len(pecas_processadas),
            'erros': len(pecas_com_erro),
            'pecas': pecas_processadas
        })
        
    except Exception as e:
        print(f"Erro no upload: {e}")
        return jsonify({'success': False, 'message': f'Erro ao processar arquivo: {str(e)}'}), 500

@app.route('/api/buscar-veiculo/<op>')
@login_required
def buscar_veiculo(op):
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Buscar veículo na tabela dados_uso_geral.dados_op
        cur.execute("""
            SELECT modelo as veiculo 
            FROM dados_uso_geral.dados_op 
            WHERE op = %s AND planta = 'Jarinu'
            LIMIT 1
        """, (op,))
        
        resultado = cur.fetchone()
        conn.close()
        
        if resultado:
            return jsonify({
                'success': True,
                'veiculo': resultado['veiculo'] or ''
            })
        else:
            return jsonify({
                'success': True,
                'veiculo': ''
            })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao buscar veículo: {str(e)}'
        }), 500

@app.route('/api/verificar-status-lotes', methods=['POST'])
@login_required
def verificar_status_lotes():
    """Verifica e atualiza o status de todos os lotes que podem estar completos"""
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Buscar todos os lotes que não estão marcados como CORTADO
        cur.execute("""
            SELECT DISTINCT id_lote 
            FROM public.plano_controle_corte_vidro2 
            WHERE (pu_cortado IS NULL OR pu_cortado != 'CORTADO')
            AND status = 'PROGRAMADO'
        """)
        lotes_pendentes = cur.fetchall()
        
        lotes_atualizados = []
        
        for lote_row in lotes_pendentes:
            lote_vd = lote_row['id_lote']
            lote_pu = 'PU' + lote_vd[2:] if len(lote_vd) >= 2 else lote_vd
            
            if verificar_e_atualizar_status_lote(lote_vd, lote_pu, cur):
                lotes_atualizados.append(lote_vd)
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'Verificação concluída. {len(lotes_atualizados)} lote(s) marcado(s) como CORTADO.',
            'lotes_atualizados': lotes_atualizados
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'}), 500

@app.route('/api/verificar-peca-existente', methods=['POST'])
@login_required
def verificar_peca_existente():
    try:
        dados = request.get_json()
        op = dados.get('op', '').strip()
        peca = dados.get('peca', '').strip()
        
        if not op or not peca:
            return jsonify({'existe': False})
        
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Verificar se peça existe no estoque, otimizadas ou manuais
        cur.execute("""
            SELECT 'estoque' as tabela, local FROM public.pu_inventory WHERE op = %s AND peca = %s
            UNION ALL
            SELECT 'otimizadas' as tabela, local FROM public.pu_otimizadas WHERE op = %s AND peca = %s AND tipo = 'PU'
            UNION ALL
            SELECT 'manuais' as tabela, local FROM public.pu_manuais WHERE op = %s AND peca = %s
            LIMIT 1
        """, (op, peca, op, peca, op, peca))
        
        resultado = cur.fetchone()
        conn.close()
        
        if resultado:
            return jsonify({
                'existe': True,
                'local': f"{resultado['tabela']}: {resultado['local']}"
            })
        else:
            return jsonify({'existe': False})
        
    except Exception as e:
        return jsonify({'existe': False, 'error': str(e)})

@app.route('/api/truncar-manuais', methods=['POST'])
@login_required
def truncar_manuais():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("TRUNCATE TABLE public.pu_manuais")
        
        # Log da ação
        cur.execute("""
            INSERT INTO public.pu_logs (usuario, acao, detalhes, data_acao)
            VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
        """, (
            current_user.username,
            'TRUNCATE_MANUAIS',
            'Limpou tabela pu_manuais'
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Tabela pu_manuais limpa com sucesso!'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'}), 500

@app.route('/api/sugerir-local-voltar', methods=['POST'])
@login_required
def sugerir_local_voltar():
    try:
        dados = request.get_json()
        op = dados.get('op', '').strip()
        peca = dados.get('peca', '').strip()
        
        if not op or not peca:
            return jsonify({'success': False, 'message': 'OP e peça são obrigatórios'})
        
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Verificar se peça está na tabela pu_exit (buscar local anterior)
        cur.execute("""
            SELECT local FROM public.pu_exit 
            WHERE op = %s AND peca = %s 
            ORDER BY data DESC 
            LIMIT 1
        """, (op, peca))
        
        exit_result = cur.fetchone()
        local_anterior = exit_result['local'] if exit_result else None
        local_anterior_disponivel = False
        
        if local_anterior:
            # Verificar se local anterior está vazio
            cur.execute("""
                SELECT COUNT(*) FROM (
                    SELECT 1 FROM public.pu_inventory WHERE local = %s
                    UNION ALL
                    SELECT 1 FROM public.pu_otimizadas WHERE local = %s AND tipo = 'PU'
                    UNION ALL
                    SELECT 1 FROM public.pu_manuais WHERE local = %s
                ) AS occupied
            """, (local_anterior, local_anterior, local_anterior))
            
            if cur.fetchone()[0] == 0:
                cur.execute("""
                    SELECT nome FROM public.pu_locais 
                    WHERE local = %s AND status = 'Ativo'
                """, (local_anterior,))
                
                if cur.fetchone():
                    local_anterior_disponivel = True
        
        # Se local anterior não disponível, sugerir novo
        if not local_anterior_disponivel:
            # Buscar locais ocupados
            cur.execute("""
                SELECT local FROM public.pu_inventory WHERE local IS NOT NULL AND local != '' 
                UNION 
                SELECT local FROM public.pu_otimizadas WHERE tipo = 'PU' AND local IS NOT NULL AND local != ''
                UNION
                SELECT local FROM public.pu_manuais WHERE local IS NOT NULL AND local != ''
            """)
            locais_ocupados = {row['local'] for row in cur.fetchall()}
            
            local_sugerido, rack_sugerido = sugerir_local_armazenamento(peca, locais_ocupados, conn)
            conn.close()
            
            if local_sugerido:
                return jsonify({
                    'success': True,
                    'local': local_sugerido,
                    'local_anterior': False
                })
            else:
                return jsonify({'success': False, 'message': 'Nenhum local disponível'})
        else:
            conn.close()
            return jsonify({
                'success': True,
                'local': local_anterior,
                'local_anterior': True
            })
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'}), 500

@app.route('/api/buscar-arquivo-sensor', methods=['POST'])
@login_required
def buscar_arquivo_sensor():
    try:
        dados = request.get_json()
        projeto = dados.get('projeto', '').strip()
        peca = dados.get('peca', '').strip()
        sensor = dados.get('sensor', '').strip()
        
        if not all([projeto, peca]):
            return jsonify({'success': False, 'message': 'Projeto e peça são obrigatórios'})
        
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Buscar arquivo baseado no projeto, peça e sensor
        if peca == 'PBS' and sensor:
            cur.execute("""
                SELECT nome_peca FROM public.arquivos_pu
                WHERE projeto = %s AND peca = %s AND sensor = %s
                LIMIT 1
            """, (projeto, peca, sensor))
        else:
            cur.execute("""
                SELECT nome_peca FROM public.arquivos_pu
                WHERE projeto = %s AND peca = %s
                LIMIT 1
            """, (projeto, peca))
        
        arquivo_result = cur.fetchone()
        conn.close()
        
        if arquivo_result:
            return jsonify({
                'success': True,
                'arquivo': arquivo_result['nome_peca']
            })
        else:
            return jsonify({
                'success': False,
                'arquivo': 'Sem arquivo de corte'
            })
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'}), 500

@app.route('/api/buscar-peca-exit/<op>/<peca>')
@login_required
def buscar_peca_exit(op, peca):
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Buscar dados na pu_exit
        cur.execute("""
            SELECT projeto, veiculo FROM public.pu_exit 
            WHERE op = %s AND peca = %s 
            ORDER BY data DESC 
            LIMIT 1
        """, (op, peca))
        
        result = cur.fetchone()
        conn.close()
        
        if result:
            return jsonify({
                'success': True,
                'projeto': result['projeto'] or '',
                'veiculo': result['veiculo'] or ''
            })
        else:
            return jsonify({'success': False, 'message': 'Peça não encontrada no histórico'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'}), 500

@app.route('/api/voltar-peca-estoque', methods=['POST'])
@login_required
def voltar_peca_estoque():
    try:
        dados = request.get_json()
        op = dados.get('op', '').strip()
        peca = dados.get('peca', '').strip()
        projeto = dados.get('projeto', '').strip()
        veiculo = dados.get('veiculo', '').strip()
        
        if not all([op, peca]):
            return jsonify({'success': False, 'message': 'OP e peça são obrigatórios'})
        
        # Se projeto ou veículo não foram fornecidos, buscar na pu_exit
        if not projeto or not veiculo:
            conn = get_db_connection()
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            
            cur.execute("""
                SELECT projeto, veiculo FROM public.pu_exit 
                WHERE op = %s AND peca = %s 
                ORDER BY data DESC 
                LIMIT 1
            """, (op, peca))
            
            exit_data = cur.fetchone()
            if exit_data:
                if not projeto:
                    projeto = exit_data['projeto'] or ''
                if not veiculo:
                    veiculo = exit_data['veiculo'] or ''
            
            conn.close()
        
        if not all([projeto, veiculo]):
            return jsonify({'success': False, 'message': 'Projeto e veículo são obrigatórios. Peça não encontrada no histórico.'})
        
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Verificar se peça já existe no sistema (dupla verificação)
        cur.execute("""
            SELECT COUNT(*) FROM (
                SELECT 1 FROM public.pu_inventory WHERE op = %s AND peca = %s
                UNION ALL
                SELECT 1 FROM public.pu_otimizadas WHERE op = %s AND peca = %s AND tipo = 'PU'
                UNION ALL
                SELECT 1 FROM public.pu_manuais WHERE op = %s AND peca = %s
            ) AS existing
        """, (op, peca, op, peca, op, peca))
        
        if cur.fetchone()[0] > 0:
            conn.close()
            return jsonify({'success': False, 'message': f'Peça {peca} com OP {op} já existe no sistema'})
        
        # Verificar se peça está na tabela pu_exit (buscar local anterior)
        cur.execute("""
            SELECT local FROM public.pu_exit 
            WHERE op = %s AND peca = %s 
            ORDER BY data DESC 
            LIMIT 1
        """, (op, peca))
        
        exit_result = cur.fetchone()
        local_anterior = exit_result['local'] if exit_result else None
        
        # Verificar se o local anterior está vazio
        local_sugerido = None
        rack_sugerido = None
        
        if local_anterior:
            # Verificar se local está vazio no estoque e otimizadas
            cur.execute("""
                SELECT COUNT(*) FROM (
                    SELECT 1 FROM public.pu_inventory WHERE local = %s
                    UNION ALL
                    SELECT 1 FROM public.pu_otimizadas WHERE local = %s AND tipo = 'PU'
                    UNION ALL
                    SELECT 1 FROM public.pu_manuais WHERE local = %s
                ) AS occupied
            """, (local_anterior, local_anterior, local_anterior))
            
            if cur.fetchone()[0] == 0:
                # Local está vazio, pode usar
                cur.execute("""
                    SELECT nome FROM public.pu_locais 
                    WHERE local = %s AND status = 'Ativo'
                """, (local_anterior,))
                
                local_info = cur.fetchone()
                if local_info:
                    local_sugerido = local_anterior
                    rack_sugerido = local_info['nome']
        
        # Se não conseguiu usar o local anterior, sugerir novo local
        if not local_sugerido:
            # Buscar todos os locais ocupados
            cur.execute("""
                SELECT local FROM public.pu_inventory WHERE local IS NOT NULL AND local != '' 
                UNION 
                SELECT local FROM public.pu_otimizadas WHERE tipo = 'PU' AND local IS NOT NULL AND local != ''
                UNION
                SELECT local FROM public.pu_manuais WHERE local IS NOT NULL AND local != ''
            """)
            locais_ocupados = {row['local'] for row in cur.fetchall()}
            
            # Sugerir novo local
            local_sugerido, rack_sugerido = sugerir_local_armazenamento(peca, locais_ocupados, conn)
        
        if not local_sugerido or not rack_sugerido:
            conn.close()
            return jsonify({'success': False, 'message': 'Não há locais disponíveis para esta peça'})
        
        # Buscar camadas da peça na tabela pu_camadas
        cur.execute("""
            SELECT l1, l3, l3_b FROM public.pu_camadas
            WHERE projeto = %s AND peca = %s
        """, (projeto, peca))
        
        camadas_result = cur.fetchone()
        camadas_para_inserir = []
        
        if camadas_result:
            l1_value = camadas_result['l1']
            l3_value = camadas_result['l3']
            l3_b_value = camadas_result.get('l3_b')
            
            # Verificar L1
            if l1_value and l1_value != '-' and str(l1_value).strip():
                try:
                    qtd_l1 = int(l1_value)
                    for _ in range(qtd_l1):
                        camadas_para_inserir.append('L1')
                except:
                    camadas_para_inserir.append('L1')
            
            # Verificar L3
            if l3_value and l3_value != '-' and str(l3_value).strip():
                try:
                    qtd_l3 = int(l3_value)
                    for _ in range(qtd_l3):
                        camadas_para_inserir.append('L3')
                except:
                    camadas_para_inserir.append('L3')
            
            # Verificar L3_B
            if l3_b_value and l3_b_value != '-' and str(l3_b_value).strip():
                try:
                    qtd_l3_b = int(l3_b_value)
                    for _ in range(qtd_l3_b):
                        camadas_para_inserir.append('L3_B')
                except:
                    camadas_para_inserir.append('L3_B')
        
        # Se não encontrou camadas, inserir sem camada
        if not camadas_para_inserir:
            camadas_para_inserir = [None]
        
        # Buscar lote da peça na tabela plano_controle_corte_vidro2
        lote_vd = ''
        lote_pu = ''
        cur.execute("""
            SELECT id_lote FROM public.plano_controle_corte_vidro2
            WHERE op = %s AND peca = %s
            LIMIT 1
        """, (op, peca))
        lote_result = cur.fetchone()
        if lote_result and lote_result['id_lote']:
            lote_vd = lote_result['id_lote']
            lote_pu = 'PU' + lote_vd[2:] if len(lote_vd) >= 2 else lote_vd
        
        # Inserir peças no estoque com as camadas
        total_inseridas = 0
        for camada in camadas_para_inserir:
            # Converter L3_B para L3 no banco (manter compatibilidade)
            camada_db = 'L3' if camada == 'L3_B' else camada
            
            cur.execute("""
                INSERT INTO public.pu_inventory (op_pai, op, peca, projeto, veiculo, local, rack, data, usuario, camada, lote_vd, lote_pu)
                VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, %s, %s, %s, %s)
            """, ('0', op, peca, projeto, veiculo, local_sugerido, rack_sugerido, current_user.username, camada_db, lote_vd, lote_pu))
            
            total_inseridas += 1
        
        # Verificar e atualizar status do lote
        if lote_vd:
            verificar_e_atualizar_status_lote(lote_vd, lote_pu, cur)
        
        # Log da ação
        cur.execute("""
            INSERT INTO public.pu_logs (usuario, acao, detalhes, data_acao)
            VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
        """, (
            current_user.username,
            'VOLTAR_PECA_ESTOQUE',
            f'Voltou peça {peca} - OP {op} ao estoque no local {local_sugerido} ({total_inseridas} camada(s))'
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'Peça {peca} voltou ao estoque com sucesso!\nLocal: {local_sugerido}\nCamadas: {total_inseridas}'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'}), 500


if __name__ == '__main__':
    import subprocess
    import threading
    import time
    
    def iniciar_dashboard():
        """Inicia o dashboard em thread separada"""
        time.sleep(2)  # Aguarda 2 segundos para o app principal iniciar
        try:
            print("Iniciando Dashboard na porta 9991...")
            subprocess.Popen(['python', 'dashboard_app.py'], cwd=os.path.dirname(os.path.abspath(__file__)))
        except Exception as e:
            print(f"Erro ao iniciar dashboard: {e}")
    
    try:
        print("Iniciando servidor Flask...")
        print("Acesse: http://10.150.16.24:9996")
        
        # Iniciar dashboard em thread separada
        dashboard_thread = threading.Thread(target=iniciar_dashboard, daemon=True)
        dashboard_thread.start()
        
        app.run(host='0.0.0.0', port=9996, debug=False, threaded=True)
    except Exception as e:
        print(f"Erro ao iniciar servidor: {e}")
        input("Pressione Enter para sair...")
        exit(1)