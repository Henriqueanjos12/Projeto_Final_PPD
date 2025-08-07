# setup.py
# Script de configuração e instalação automática

import subprocess
import sys
import os
import platform
import time


def executar_comando(comando):
    """Executa comando no sistema e retorna sucesso/falha"""
    try:
        result = subprocess.run(comando, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)


def verificar_python():
    """Verifica versão do Python"""
    print("🔍 Verificando versão do Python...")
    version = sys.version_info

    if version.major >= 3 and version.minor >= 7:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} - OK")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} - Versão muito antiga")
        print("   Necessário Python 3.7 ou superior")
        return False


def instalar_dependencias_python():
    """Instala dependências Python"""
    print("\n📦 Instalando dependências Python...")

    dependencias = [
        "Pyro5==5.14",
        "pika==1.3.2",
        "geopy==2.3.0"
    ]

    for dep in dependencias:
        print(f"Instalando {dep}...")
        sucesso, stdout, stderr = executar_comando(f"{sys.executable} -m pip install {dep}")

        if sucesso:
            print(f"✅ {dep} instalado com sucesso")
        else:
            print(f"❌ Erro ao instalar {dep}: {stderr}")
            return False

    return True


def verificar_rabbitmq():
    """Verifica se RabbitMQ está instalado e rodando"""
    print("\n🐰 Verificando RabbitMQ...")

    # Tentar conectar
    try:
        import pika
        connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        connection.close()
        print("✅ RabbitMQ está rodando")
        return True
    except ImportError:
        print("❌ Pika não instalado")
        return False
    except Exception:
        print("❌ RabbitMQ não está rodando ou não está instalado")
        return False


def instalar_rabbitmq():
    """Tenta instalar RabbitMQ baseado no sistema operacional"""
    print("\n🔧 Tentando instalar RabbitMQ...")

    sistema = platform.system().lower()

    if sistema == "linux":
        # Detectar distribuição
        try:
            with open("/etc/os-release", "r") as f:
                os_info = f.read().lower()

            if "ubuntu" in os_info or "debian" in os_info:
                print("Detectado Ubuntu/Debian")
                comandos = [
                    "sudo apt-get update",
                    "sudo apt-get install -y rabbitmq-server",
                    "sudo systemctl enable rabbitmq-server",
                    "sudo systemctl start rabbitmq-server"
                ]
            elif "centos" in os_info or "rhel" in os_info or "fedora" in os_info:
                print("Detectado CentOS/RHEL/Fedora")
                comandos = [
                    "sudo yum install -y rabbitmq-server",
                    "sudo systemctl enable rabbitmq-server",
                    "sudo systemctl start rabbitmq-server"
                ]
            else:
                print("Distribuição Linux não reconhecida")
                print("Por favor, instale RabbitMQ manualmente:")
                print("https://www.rabbitmq.com/install-debian.html")
                return False

        except FileNotFoundError:
            print("Não foi possível detectar a distribuição Linux")
            return False

    elif sistema == "darwin":  # macOS
        print("Detectado macOS")
        # Verificar se Homebrew está instalado
        homebrew_installed, _, _ = executar_comando("which brew")

        if homebrew_installed:
            comandos = [
                "brew install rabbitmq",
                "brew services start rabbitmq"
            ]
        else:
            print("Homebrew não encontrado. Por favor, instale o Homebrew primeiro:")
            print("https://brew.sh/")
            return False

    elif sistema == "windows":
        print("Detectado Windows")
        print("Para Windows, recomendamos instalar via Docker ou manualmente:")
        print("1. Docker: docker run -d --hostname my-rabbit --name some-rabbit -p 5672:5672 rabbitmq:3")
        print("2. Manual: https://www.rabbitmq.com/install-windows.html")
        return False

    else:
        print(f"Sistema operacional {sistema} não suportado")
        return False

    # Executar comandos de instalação
    for comando in comandos:
        print(f"Executando: {comando}")
        sucesso, stdout, stderr = executar_comando(comando)

        if not sucesso:
            print(f"❌ Erro ao executar: {comando}")
            print(f"Erro: {stderr}")
            return False

        time.sleep(2)

    print("✅ RabbitMQ instalado com sucesso")
    return True


def criar_arquivos_projeto():
    """Cria arquivos necessários do projeto"""
    print("\n📁 Criando arquivos do projeto...")

    # requirements.txt
    requirements_content = """Pyro5==5.14
pika==1.3.2
geopy==2.3.0
"""

    with open("requirements.txt", "w") as f:
        f.write(requirements_content)
    print("✅ requirements.txt criado")

    # README.md básico
    readme_content = """# Sistema de Comunicação Baseado em Localização

## Execução Rápida

1. Execute o setup: `python setup.py`
2. Execute o exemplo: `python exemplo_completo.py`
3. Ou execute o sistema principal: `python comunicacao_sistema.py`

## Dependências

- Python 3.7+
- RabbitMQ
- Bibliotecas Python listadas em requirements.txt

Para mais detalhes, consulte a documentação completa.
"""

    with open("README.md", "w") as f:
        f.write(readme_content)
    print("✅ README.md criado")

    return True


def verificar_portas():
    """Verifica se as portas necessárias estão disponíveis"""
    print("\n🔌 Verificando disponibilidade de portas...")

    # Portas do RabbitMQ (5672) e aplicação (8001-8004, 9001-9004)
    portas_app = [8001, 8002, 8003, 8004, 9001, 9002, 9003, 9004]
    porta_rabbitmq = 5672

    import socket

    portas_app_ocupadas = []

    # Verificar portas da aplicação
    for porta in portas_app:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        resultado = sock.connect_ex(('localhost', porta))
        sock.close()

        if resultado == 0:
            portas_app_ocupadas.append(porta)

    # Verificar porta RabbitMQ (deve estar ocupada se funcionando)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    rabbitmq_rodando = sock.connect_ex(('localhost', porta_rabbitmq)) == 0
    sock.close()

    if rabbitmq_rodando:
        print(f"✅ RabbitMQ rodando na porta {porta_rabbitmq}")
    else:
        print(f"⚠️ RabbitMQ não está rodando na porta {porta_rabbitmq}")

    if portas_app_ocupadas:
        print(f"⚠️ Portas da aplicação ocupadas: {portas_app_ocupadas}")
        print("   Isso pode causar conflitos. Considere parar outros serviços.")
        return False
    else:
        print("✅ Todas as portas da aplicação estão disponíveis")
        return True


def criar_script_execucao():
    """Cria script de execução simplificado"""
    print("\n📜 Criando script de execução...")

    # Para sistemas Unix
    if platform.system() != "Windows":
        script_content = """#!/bin/bash
echo "Iniciando Sistema de Comunicação Baseado em Localização..."
echo "Verificando RabbitMQ..."

if ! pgrep -x "rabbitmq-server" > /dev/null; then
    echo "Iniciando RabbitMQ..."
    if command -v systemctl > /dev/null; then
        sudo systemctl start rabbitmq-server
    elif command -v brew > /dev/null; then
        brew services start rabbitmq
    else
        echo "Por favor, inicie o RabbitMQ manualmente"
        exit 1
    fi
    sleep 3
fi

echo "Executando sistema..."
python3 exemplo_completo.py
"""

        with open("executar.sh", "w") as f:
            f.write(script_content)

        # Tornar executável
        os.chmod("executar.sh", 0o755)
        print("✅ executar.sh criado")

    # Para Windows
    script_windows = """@echo off
echo Iniciando Sistema de Comunicacao Baseado em Localizacao...
echo Verificando RabbitMQ...

tasklist /FI "IMAGENAME eq erl.exe" 2>NUL | find /I /N "erl.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo RabbitMQ ja esta rodando
) else (
    echo Por favor, inicie o RabbitMQ manualmente
    echo Ou use Docker: docker run -d --name rabbitmq -p 5672:5672 rabbitmq:3
    pause
)

echo Executando sistema...
python exemplo_completo.py
pause
"""

    with open("executar.bat", "w") as f:
        f.write(script_windows)
    print("✅ executar.bat criado")

    return True


def testar_instalacao():
    """Testa se tudo foi instalado corretamente"""
    print("\n🧪 Testando instalação...")

    # Teste 1: Imports
    try:
        import Pyro5.api
        import pika
        from geopy.distance import geodesic
        print("✅ Todas as bibliotecas importadas com sucesso")
    except ImportError as e:
        print(f"❌ Erro ao importar bibliotecas: {e}")
        return False

    # Teste 2: RabbitMQ
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        channel = connection.channel()
        channel.queue_declare(queue='test_queue')
        channel.basic_publish(exchange='', routing_key='test_queue', body='test')
        connection.close()
        print("✅ RabbitMQ funcionando corretamente")
    except Exception as e:
        print(f"❌ Erro no RabbitMQ: {e}")
        return False

    # Teste 3: Cálculo de distância
    try:
        dist = geodesic((-3.7319, -38.5267), (-3.7350, -38.5200)).kilometers
        print(f"✅ Cálculo de distância funcionando: {dist:.2f}km")
    except Exception as e:
        print(f"❌ Erro no cálculo de distância: {e}")
        return False

    print("✅ Todos os testes passaram!")
    return True


def menu_principal():
    """Menu principal do setup"""
    print("SISTEMA DE COMUNICAÇÃO BASEADO EM LOCALIZAÇÃO - SETUP")
    print("=" * 55)

    opcoes = [
        ("Instalação completa (recomendado)", instalacao_completa),
        ("Verificar apenas dependências", verificar_apenas),
        ("Instalar apenas Python packages", instalar_dependencias_python),
        ("Instalar apenas RabbitMQ", configurar_rabbitmq),
        ("Testar instalação existente", testar_instalacao),
        ("Criar scripts de execução", criar_script_execucao),
        ("Sair", None)  # None indica função especial
    ]

    while True:
        print(f"\nEscolha uma opção:")
        for i, (desc, _) in enumerate(opcoes, 1):
            print(f"{i}. {desc}")

        try:
            escolha = int(input("\nSua escolha (1-{}): ".format(len(opcoes))).strip())

            if 1 <= escolha <= len(opcoes):
                desc, funcao = opcoes[escolha - 1]

                if funcao is None:  # Opção sair
                    print("👋 Saindo do setup...")
                    return True  # Sair com sucesso

                resultado = funcao()

                if resultado:
                    print("\n✅ Operação concluída com sucesso!")
                else:
                    print("\n❌ Operação falhou. Verifique as mensagens de erro acima.")

                input("\nPressione Enter para continuar...")
            else:
                print("❌ Opção inválida!")

        except ValueError:
            print("❌ Por favor, digite um número válido!")
        except KeyboardInterrupt:
            print("\n👋 Setup interrompido pelo usuário.")
            return True


def instalacao_completa():
    """Executa instalação completa do sistema"""
    print("\n🚀 INSTALAÇÃO COMPLETA")
    print("=" * 30)

    etapas = [
        ("Verificando Python", verificar_python),
        ("Instalando dependências Python", instalar_dependencias_python),
        ("Configurando RabbitMQ", configurar_rabbitmq),
        ("Verificando portas", verificar_portas),
        ("Criando arquivos do projeto", criar_arquivos_projeto),
        ("Criando scripts de execução", criar_script_execucao),
        ("Testando instalação", testar_instalacao)
    ]

    for desc, funcao in etapas:
        print(f"\n⏳ {desc}...")
        if not funcao():
            print(f"❌ Falha em: {desc}")
            return False
        time.sleep(1)

    print("\n🎉 INSTALAÇÃO COMPLETA CONCLUÍDA COM SUCESSO!")
    print("\nPróximos passos:")
    print("1. Execute: python exemplo_completo.py")
    print("2. Ou use os scripts: ./executar.sh (Linux/Mac) ou executar.bat (Windows)")
    print("3. Para desenvolvimento: python comunicacao_sistema.py")

    return True


def verificar_apenas():
    """Apenas verifica dependências sem instalar"""
    print("\n🔍 VERIFICAÇÃO DE DEPENDÊNCIAS")
    print("=" * 35)

    verificacoes = [
        ("Python", verificar_python),
        ("RabbitMQ", verificar_rabbitmq),
        ("Portas", verificar_portas)
    ]

    tudo_ok = True

    for desc, funcao in verificacoes:
        print(f"\n🔍 Verificando {desc}...")
        if not funcao():
            tudo_ok = False

    if tudo_ok:
        print("\n✅ Todas as dependências estão OK!")
    else:
        print("\n❌ Algumas dependências precisam ser resolvidas.")
        print("Use a opção 'Instalação completa' para resolver automaticamente.")

    return tudo_ok


def configurar_rabbitmq():
    """Configura RabbitMQ (verifica ou instala)"""
    if verificar_rabbitmq():
        return True

    print("RabbitMQ não encontrado. Tentando instalar...")

    resposta = input("Deseja tentar instalar automaticamente? (s/N): ").strip().lower()

    if resposta in ['s', 'sim', 'y', 'yes']:
        return instalar_rabbitmq()
    else:
        print("\nInstalação manual do RabbitMQ:")
        print("Ubuntu/Debian: sudo apt-get install rabbitmq-server")
        print("CentOS/RHEL: sudo yum install rabbitmq-server")
        print("macOS: brew install rabbitmq")
        print("Windows: https://www.rabbitmq.com/install-windows.html")
        print("Docker: docker run -d --name rabbitmq -p 5672:5672 rabbitmq:3")
        return False


def main():
    """Função principal"""
    try:
        menu_principal()
    except KeyboardInterrupt:
        print("\n\n👋 Setup interrompido. Até logo!")
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        print("Por favor, execute novamente ou instale manualmente.")


if __name__ == "__main__":
    main()