#!/bin/bash

# Установка зависимостей
echo "Установка зависимостей..."
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv golang-go git curl

# Клонирование репозитория
echo "Клонирование репозитория..."
if [ -d "cyberchat" ]; then
    echo "Директория cyberchat уже существует. Обновляем репозиторий..."
    cd cyberchat
    git pull
else
    git clone https://github.com/hhu67/cyberchat.git
    cd cyberchat
fi

# Создание и активация виртуального окружения для Python
echo "Создание виртуального окружения для Python..."
python3 -m venv venv
source venv/bin/activate

# Установка Python зависимостей
echo "Установка Python зависимостей..."
pip install --upgrade pip
pip install -r client_py/requirements.txt

# Компиляция Go кода
echo "Компиляция Go кода..."
cd backend_go
if [ ! -f "go.mod" ]; then
    go mod init cyberchat
fi
go build -o cyberchat
cd ..

# Копирование бинарника в /usr/local/bin
echo "Копирование бинарника в /usr/local/bin..."
sudo cp backend_go/cyberchat /usr/local/bin/cyberchat
sudo chmod +x /usr/local/bin/cyberchat

# Добавление команды в ~/.bashrc
echo "Добавление команды в ~/.bashrc..."
echo 'alias cyberchat=\"cyberchat\"' >> ~/.bashrc
source ~/.bashrc

echo "Установка завершена! Теперь вы можете запускать проект командой 'cyberchat'."