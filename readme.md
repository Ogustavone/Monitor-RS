Monitor RS - Sistema de Monitoramento Hidrológico
===============================================

Resumo
------
Pequeno dashboard Streamlit para monitoramento da bacia do Guaíba (Canoas / Porto Alegre - RS).
Exibe: mapa interativo, previsão do tempo (Open-Meteo) e alertas/notícias (Google News RSS).

Estrutura
---------
- app.py              -> entrada do Streamlit
- components/iframe.py -> componente do mapa interativo
- components/clima.py  -> componente de clima (Open-Meteo)
- components/noticias.py -> busca e exibição de notícias/alertas

Como rodar
----------
1. Instale dependências (recomendado em venv):
	pip install -r requirements.txt

2. Execute o app:
	streamlit run app.py

Notas
-----
- A localização usada para o clima está em LAT/LON definidos em components/clima.py.
- As notícias são buscadas via Google News RSS e filtradas por termos e geolocalização.
- Ajuste tempos de cache e limites dentro dos arquivos de componente conforme necessário.

Licença
-------
Projeto pessoal — sem licença explícita. Use conforme apropriado.

