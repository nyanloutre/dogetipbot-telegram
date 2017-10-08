from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import ParseMode
from block_io import BlockIo, BlockIoAPIError
import logging
import os

BLOCK_IO_API_KEY = os.environ['BLOCK_IO_API_KEY']
BLOCK_IO_PIN = os.environ['BLOCK_IO_PIN']
TELEGRAM_API_KEY = os.environ['TELEGRAM_API_KEY']
NETWORK = os.environ['NETWORK']

# Logging

logging.basicConfig(level=logging.ERROR,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Exceptions

class NoAccountError(Exception):
    pass

class NotEnoughDoge(Exception):
    pass

class AccountExisting(Exception):
    pass

# BlockIO

version = 2
block_io = BlockIo(BLOCK_IO_API_KEY, BLOCK_IO_PIN, version)

# Core functions

def get_balance(account):
    try:
        response = block_io.get_address_by(label=account)
    except BlockIoAPIError:
        raise NoAccountError(account)
    else:
        return (float(response['data']['available_balance']), float(response['data']['pending_received_balance']))

def create_address(account):
    try:
        response = block_io.get_new_address(label=account)
    except BlockIoAPIError:
        raise AccountExisting
    else:
        return response['data']['address']

def get_address(account):
    try:
        response = block_io.get_address_by(label=account)
    except BlockIoAPIError:
        raise NoAccountError(account)
    else:
        return response['data']['address']

def transaction(sender, receiver, amount):
    try:
        if get_balance(sender)[0] > amount:
            address_receiver = get_address(receiver)
            return block_io.withdraw_from_labels(amounts=amount, from_labels=sender, to_labels=receiver, priority="low")
        else:
            raise NotEnoughDoge
    except NoAccountError:
        raise

def address_transaction(account, address, amount):
    try:
        if get_balance(account)[0] > amount:
            return block_io.withdraw_from_labels(amounts=amount, from_labels=account, to_addresses=address, priority="low")
        else:
            return NotEnoughDoge
    except NoAccountError:
        raise

# Telegram functions

def start(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text="Bark ! Je suis un tipbot Dogecoin ! \n\n Pour commencer envoyez moi /register")

def dogetip(bot, update, args):
    try:
        montant = int(args[0])
        unit = args[1]
        destinataire = args[2][1:]
    except (IndexError, ValueError):
        bot.send_message(chat_id=update.message.chat_id, text="Syntaxe : /dogetip xxx doge @destinataire")
    else:
        try:
            if unit == "doge":
                response = transaction(update.message.from_user.username, destinataire, montant)
        except NotEnoughDoge:
            message = "Pas assez de doge @" + update.message.from_user.username
        except NoAccountError as e:
            message = "Vous n'avez pas de compte @" + str(e) + '\n\n' \
                    + "Utilisez /register pour démarrer"
        else:
            txid = response['data']['txid']
            message = '🚀 Transaction effectuée 🚀\n\n' \
                    + str(montant) + ' ' + NETWORK + '\n' \
                    + '@' + update.message.from_user.username + ' → @' + destinataire + '\n\n' \
                    + '<a href="https://chain.so/tx/' + NETWORK + '/' + txid + '">Voir la transaction</a>'

        bot.send_message(chat_id=update.message.chat_id, parse_mode=ParseMode.HTML, text=message)

def register(bot, update):
    try:
        address = create_address(update.message.from_user.username)
    except AccountExisting:
        bot.send_message(chat_id=update.message.chat_id, text="Vous avez déjà un compte")
    else:
        bot.send_message(chat_id=update.message.chat_id, text=address)

def infos(bot, update):
    try:
        address = get_address(update.message.from_user.username)
        balance, unconfirmed_balance = get_balance(update.message.from_user.username)
    except NoAccountError as e:
        bot.send_message(chat_id=update.message.chat_id, text="Vous n'avez pas de compte @" + str(e) + '\n\n' + "Utilisez /register pour démarrer")
    else:
        bot.send_message(chat_id=update.message.chat_id, text=address + "\n\n" + str(balance) + " " + NETWORK + "\n" + str(unconfirmed_balance) + " " + NETWORK + " unconfirmed")

def withdraw(bot, update, args):
    montant = int(args[0])
    unit = args[1]
    address = args[2]

    if unit == "doge":
        response = address_transaction(update.message.from_user.username, address, montant)

    txid = response['data']['txid']

    bot.send_message(chat_id=update.message.chat_id, parse_mode=ParseMode.MARKDOWN, text="Transaction effectuée !\n [tx](https://chain.so/tx/" + NETWORK + "/" + txid + ")")

def testing(bot, update):
    bot.send_message(chat_id=update.message.chat_id, parse_mode=ParseMode.MARKDOWN, text="Bonjour @V_IAL")

# Telegram initialisation

updater = Updater(token=TELEGRAM_API_KEY)
dispatcher = updater.dispatcher

start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)

dogetip_handler = CommandHandler('dogetip', dogetip, pass_args=True)
dispatcher.add_handler(dogetip_handler)

register_handler = CommandHandler('register', register)
dispatcher.add_handler(register_handler)

infos_handler = CommandHandler('infos', infos)
dispatcher.add_handler(infos_handler)

withdraw_handler = CommandHandler('withdraw', withdraw, pass_args=True)
dispatcher.add_handler(withdraw_handler)

testing_handler = CommandHandler('testing', testing)
dispatcher.add_handler(testing_handler)

updater.start_polling()
updater.idle()
