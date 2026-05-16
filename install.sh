#!/bin/bash

# Установка зависимостей
echo "Установка зависимостей..."
sudo apt-get update
sudo apt-get install -y python3 python3-pip golang-go git curl

# Клонирование репозитория
echo "Клонирование репозитория..."
git clone https://github.com/hhu67/cyberchat.git
cd cyberchat

# Установка Python зависимостей
echo "Установка Python зависимостей..."
pip3 install -r client_py/requirements.txt

# Компиляция Go кода
echo "Компиляция Go кода..."
cd backend_go
go build -o cyberchat
cd ..

# Копирование бинарника в /usr/local/bin
echo "Копирование бинарника в /usr/local/bin..."
sudo cp backend_go/cyberchat /usr/local/bin/cyberchat

# Добавление команды в ~/.bashrc
echo "Добавление команды в ~/.bashrc..."
echo 'alias cyberchat="cyberchat"' >> ~/.bashrc
source ~/.bashrc

echo "Установка завершена! Теперь вы можете запускать проект командой 'cyberchat'."
