from flask import Flask, render_template, jsonify, request, send_file
import psycopg2
import psycopg2.pool
import os
from dotenv import load_dotenv
import time
import io
from datetime import datetime

load_dotenv()

app = Flask(__name__)

@app.route('/')
def dashboard():
    return render_template('dashboard_standalone.html')

@app.route('/api/dashboard-producao')
def api_dashboard_producao():
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PSW'),
            port=os.getenv('DB_PORT', 5432)
        )
        cursor = conn.cursor()
        
        # Get stock pieces grouped by PEÇA+OP
        query_estoque = """
        SELECT 
            i.op,
            i.peca,
            i.projeto,
            COALESCE(d.modelo, i.veiculo) as veiculo,
            STRING_AGG(DISTINCT i.local, ', ' ORDER BY i.local) as locais,
            COUNT(*) as quantidade,
            COALESCE(UPPER(d.etapa), 'PEÇA NÃO ESTÁ NO PPLUG OU FOI APROVADA IF') as etapa,
            COALESCE(UPPER(d.prioridade), 'NORMAL') as prioridade
        FROM pu_inventory i
        LEFT JOIN dados_uso_geral.dados_op d ON i.op::text = d.op::text AND i.peca = d.item AND d.planta = 'Jarinu'
        GROUP BY i.op, i.peca, i.projeto, COALESCE(d.modelo, i.veiculo), d.etapa, d.prioridade
        ORDER BY MAX(i.id) DESC
        """
        
        cursor.execute(query_estoque)
        resultados_estoque = cursor.fetchall()
        
        # Get pieces in production stages that are NOT in stock OR otimizadas
        query_forno = """
        WITH rt_rp_recentes AS (
            SELECT DISTINCT 
                CAST(a.op AS TEXT) as op,
                a.item as peca
            FROM public.apontamento_pplug_jarinu a
            WHERE UPPER(TRIM(a.etapa)) = 'RT-RP'
            AND a.data >= CURRENT_TIMESTAMP - INTERVAL '24 hours'
        )
        SELECT DISTINCT
            d.op,
            d.item as peca,
            COALESCE(d.codigo_veiculo, d.produto) as projeto,
            d.modelo as veiculo,
            UPPER(d.etapa) as etapa,
            COALESCE(UPPER(d.prioridade), 'NORMAL') as prioridade
        FROM dados_uso_geral.dados_op d
        WHERE UPPER(d.etapa) IN ('CORTE', 'LAPIDACAO', 'SERIGRAFIA', 'SINTERIZACAO', 'EMPOLVADO', 'BUFFER', 'FORNO-S', 'RESFRIAMENTO', 'POS-FORNO', 'ACO', 'CORTE-CURVO', 'PRE-MONTAGEM', 'MONTAGEM')
        AND d.planta = 'Jarinu'
        AND NOT EXISTS (
            SELECT 1 FROM pu_inventory i 
            WHERE i.op::text = d.op::text AND i.peca = d.item
        )
        AND NOT EXISTS (
            SELECT 1 FROM pu_otimizadas o 
            WHERE o.op::text = d.op::text AND o.peca = d.item AND o.tipo = 'PU'
        )
        AND NOT EXISTS (
            SELECT 1 FROM pu_exit e 
            WHERE e.op::text = d.op::text AND e.peca = d.item
            AND e.data >= NOW() - INTERVAL '24 hours'
        )
        AND NOT EXISTS (
            SELECT 1 FROM rt_rp_recentes r
            WHERE r.op = CAST(d.op AS TEXT) AND r.peca = d.item
        )
        ORDER BY d.op, d.item
        """
        
        # Debug: verificar apontamentos RT-RP recentes
        debug_query = """
        SELECT DISTINCT
            CAST(a.op AS TEXT) as op,
            a.item,
            TRIM(a.etapa) as etapa,
            a.data,
            EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - a.data))/3600 as horas_atras
        FROM public.apontamento_pplug_jarinu a
        WHERE UPPER(TRIM(a.etapa)) = 'RT-RP'
        AND a.data >= CURRENT_TIMESTAMP - INTERVAL '24 hours'
        ORDER BY a.data DESC
        """
        cursor.execute(debug_query)
        debug_results = cursor.fetchall()
        print(f"DEBUG RT-RP últimas 24h: {debug_results}")
        
        cursor.execute(query_forno)
        resultados_forno = cursor.fetchall()
        
        dados = []
        
        # Process stock pieces
        for row in resultados_estoque:
            etapa = row[6]
            prioridade = row[7]
            status = 'normal'
            if etapa in ['INSPECAO FINAL', 'BUFFER-AUTOCLAVE', 'AUTOCLAVE', 'EMBOLSADO']:
                status = 'critico'
            elif etapa in ['PRE-MONTAGEM', 'PREMONTAGEM']:
                status = 'aviso'
            elif etapa == 'PEÇA NÃO ESTÁ NO PPLUG OU FOI APROVADA IF':
                status = 'critico'
            
            if etapa == 'BUFFER-AUTOCLAVE':
                etapa = 'BUFFER-ACV'

            if etapa == 'INSPECAO FINAL':
                etapa = 'INSP FINAL'
            
            dados.append({
                'op': row[0] or '',
                'peca': row[1] or '',
                'projeto': row[2] or '',
                'veiculo': row[3] or '',
                'local': row[4] or '',
                'quantidade': row[5],
                'etapa': etapa,
                'prioridade': prioridade,
                'status': status
            })
        
        # Process production stage pieces not in stock AND not in otimizadas
        for row in resultados_forno:
            etapa = row[4]
            prioridade = row[5]
            status = 'forno'
            if etapa in ['CORTE', 'LAPIDACAO', 'SERIGRAFIA']:
                status = 'normal'
            elif etapa in ['SINTERIZACAO', 'EMPOLVADO', 'BUFFER']:
                status = 'aviso'
            
            dados.append({
                'op': row[0] or '',
                'peca': row[1] or '',
                'projeto': row[2] or '',
                'veiculo': row[3] or '',
                'local': etapa,
                'quantidade': 1,
                'etapa': etapa,
                'prioridade': prioridade,
                'status': status
            })
        
        cursor.close()
        conn.close()
        
        return jsonify(dados)
        
    except Exception as e:
        print(f"Dashboard error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/gerar-relatorio-dashboard', methods=['POST'])
def gerar_relatorio_dashboard():
    try:
        # Verificar se pandas está disponível
        try:
            import pandas as pd
        except ImportError:
            return jsonify({'error': 'Pandas não está instalado no servidor'}), 500
        
        dados = request.json.get('dados', [])
        
        if not dados:
            return jsonify({'error': 'Nenhum dado fornecido'}), 400
        
        # Adicionar coluna "Tipo" baseada no status
        for item in dados:
            status = item.get('status', '')
            if status == 'aviso':
                item['tipo'] = 'Peças na Pré-Montagem'
            elif status == 'forno':
                item['tipo'] = 'Peças no Forno e Montagem sem PU (Estoque + Otimizadas)'
            elif status == 'critico':
                item['tipo'] = 'Peças que já passaram da Montagem'
            else:
                item['tipo'] = 'Outros'
        
        # Converter dados para DataFrame
        df = pd.DataFrame(dados)
        
        # Reordenar colunas incluindo "Tipo"
        colunas_ordenadas = ['tipo', 'op', 'peca', 'projeto', 'veiculo', 'local', 'quantidade', 'etapa', 'prioridade', 'status']
        df = df.reindex(columns=colunas_ordenadas)
        
        # Renomear colunas para português
        df.columns = ['Tipo', 'OP', 'Peça', 'Projeto', 'Veículo', 'Local', 'Quantidade', 'Etapa', 'Prioridade', 'Status']
        
        # Criar arquivo Excel em memória
        output = io.BytesIO()
        try:
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Dashboard', index=False)
                
                # Ajustar largura das colunas
                worksheet = writer.sheets['Dashboard']
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 50)
                    worksheet.column_dimensions[column_letter].width = adjusted_width
        except ImportError:
            return jsonify({'error': 'OpenPyXL não está instalado no servidor'}), 500
        
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'relatorio_dashboard_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        )
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Erro detalhado ao gerar relatório dashboard: {error_details}")
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9991, debug=False)