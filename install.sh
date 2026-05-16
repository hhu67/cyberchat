#!/bin/bash

# Установка зависимостей
echo "Установка зависимостей..."
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv golang-go git curl

# Клонирование или обновление репозитория
echo "Обновление репозитория..."
if [ -d "cyberchat" ]; then
    echo "Директория cyberchat уже существует. Обновляем репозиторий..."
    cd cyberchat
    git pull
else
    git clone https://github.com/hhu67/cyberchat.git
    cd cyberchat
fi

# Создание и активация виртуального окружения для Python
echo "Настройка виртуального окружения для Python..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
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

# Добавление команды в ~/.bashrc (если ещё не добавлена)
if ! grep -q "alias cyberchat" ~/.bashrc; then
    echo "Добавление команды в ~/.bashrc..."
    echo 'alias cyberchat=\"cyberchat\"' >> ~/.bashrc
fi
source ~/.bashrc

echo "Обновление завершено! Теперь вы можете запускать проект командой 'cyberchat'."