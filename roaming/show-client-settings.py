#!/usr/bin/env python3
"""Show the travel SIP credential locally, never on stdout or in command arguments."""
import subprocess
args=['/usr/bin/python3','/home/gateway/asterisk/linphone-push/keyring_credentials.py','lookup','--host','home.example.net','--username','1003','--kind','travel-sip']
r=subprocess.run(args,capture_output=True,text=True,check=True)
text='''Linphone → аватар → Добавить аккаунт → Сторонняя SIP-учётная запись

Имя пользователя: 1003
Домен: home.example.net
Транспорт: TLS
Имя для отображения: Домашняя SIM
Пароль: '''+r.stdout+'''

Сохраните прежний аккаунт traveler-example: он нужен для входящих и push.
Шифрование звонков: SRTP, обязательно.
Для исходящих выбирайте новую линию «Домашняя SIM».

Пароль хранится в связке ключей компьютера, в переписку его присылать не нужно.
'''
subprocess.run(['zenity','--text-info','--title=Настройки Linphone: домашняя SIM','--width=720','--height=420','--font=Monospace 12'],input=text,text=True,stdout=subprocess.DEVNULL,check=True)
