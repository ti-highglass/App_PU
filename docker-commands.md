# Comandos Docker - Sistema Alocação PU

## 1. Construir a imagem
```bash
docker build -t sistema-pu:latest .
```

## 2. Salvar imagem como arquivo .tar
```bash
docker save -o sistema-pu.tar sistema-pu:latest
```

## 3. Carregar imagem do arquivo .tar (no servidor)
```bash
docker load -i sistema-pu.tar
```

## 4. Executar container
```bash
docker run -d \
  --name sistema-pu \
  -p 9995:9995 \
  --env-file .env \
  sistema-pu:latest
```

## 5. Ver logs do container
```bash
docker logs sistema-pu
```

## 6. Parar/Iniciar container
```bash
docker stop sistema-pu
docker start sistema-pu
```

## 7. Remover container
```bash
docker rm -f sistema-pu
```