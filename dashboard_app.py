from flask import Flask, render_template, jsonify
import psycopg2
import psycopg2.pool
import os
from dotenv import load_dotenv
import time

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
            i.veiculo,
            STRING_AGG(DISTINCT i.local, ', ' ORDER BY i.local) as locais,
            COUNT(*) as quantidade,
            COALESCE(UPPER(d.etapa), 'IF') as etapa,
            COALESCE(UPPER(d.prioridade), 'NORMAL') as prioridade
        FROM pu_inventory i
        LEFT JOIN dados_uso_geral.dados_op d ON i.op::text = d.op::text AND i.peca = d.item AND d.planta = 'Jarinu'
        GROUP BY i.op, i.peca, i.projeto, i.veiculo, d.etapa, d.prioridade
        ORDER BY MAX(i.id) DESC
        """
        
        cursor.execute(query_estoque)
        resultados_estoque = cursor.fetchall()
        
        # Get pieces in FORNO-S and MONTAGEM that are NOT in stock
        query_forno = """
        SELECT DISTINCT
            d.op,
            d.item as peca,
            d.produto as projeto,
            '' as veiculo,
            UPPER(d.etapa) as etapa,
            COALESCE(UPPER(d.prioridade), 'NORMAL') as prioridade
        FROM dados_uso_geral.dados_op d
        WHERE UPPER(d.etapa) IN ('FORNO-S', 'MONTAGEM')
        AND d.planta = 'Jarinu'
        AND NOT EXISTS (
            SELECT 1 FROM pu_inventory i 
            WHERE i.op::text = d.op::text AND i.peca = d.item
        )
        AND NOT EXISTS (
            SELECT 1 FROM pu_exit e 
            WHERE e.op::text = d.op::text AND e.peca = d.item
            AND e.data >= NOW() - INTERVAL '8 hours'
        )
        ORDER BY d.op, d.item
        """
        
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
            elif etapa == 'IF':
                status = 'critico'
            
            if etapa == 'BUFFER-AUTOCLAVE':
                etapa = 'BUFFER-ACV'
            
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
        
        # Process FORNO-S and MONTAGEM pieces not in stock
        for row in resultados_forno:
            etapa = row[4]
            prioridade = row[5]
            dados.append({
                'op': row[0] or '',
                'peca': row[1] or '',
                'projeto': row[2] or '',
                'veiculo': row[3] or '',
                'local': etapa,
                'quantidade': 1,
                'etapa': etapa,
                'prioridade': prioridade,
                'status': 'forno'
            })
        
        cursor.close()
        conn.close()
        
        return jsonify(dados)
        
    except Exception as e:
        print(f"Dashboard error: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9991, debug=False)