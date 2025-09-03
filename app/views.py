from bitshares.account import Account
from bitshares import BitShares
import re
from pprint import pprint
import json
import os
from flask import render_template, request, session, jsonify, abort
from . import app, models
from datetime import datetime
import traceback
from . import config
from graphenebase.account import PasswordKey
log = app.logger


def api_error(msg):
    return jsonify({"error": {"base": [msg]}})


@app.route('/')
def index():
    return request.args.get("ip")


@app.route('/api/v1/accounts', methods=['POST'], defaults={'referrer': None})
@app.route('/<referrer>/api/v1/accounts', methods=['POST'])
def tapbasic(referrer):
    # test is request has 'account' key
    if not request.json or 'account' not in request.json:
        abort(400)
    account = request.json.get('account', {})

    # make sure all keys are present
    if any([key not in account
            for key in ["active_key", "memo_key", "owner_key", "name"]]):
        abort(400)

    if len(models.Accounts.query.options().all()) >= config.registrations_limit:
        return api_error("Registration limit achieved")

    # prevent massive account registration
    if request.args.get("ip") != "127.0.0.1" and models.Accounts.exists(request.args.get("ip")):
        return api_error("Only one account per IP")

    # Check if account name is cheap name
    if (not re.search(r"[0-9-]", account["name"]) and
            re.search(r"[aeiouy]", account["name"])):
        return api_error("Only cheap names allowed!")

    # This is not really needed but added to keep API-compatibility with Rails Faucet
    account.update({"id": None})

    bitshares = BitShares(
        config.witness_url,
        nobroadcast=config.nobroadcast,
        keys=[config.wif],
        prefix=config.prefix
    )

    try:
        Account(account["name"], bitshares_instance=bitshares)
        return api_error("Account exists")
    except:
        pass

    # Registrar
    registrar = account.get("registrar", config.registrar) or config.registrar
    try:
        registrar = Account(registrar, bitshares_instance=bitshares)
    except:
        return api_error("Unknown registrar: %s" % registrar)

    # Referrer
    referrer = account.get("referrer", config.default_referrer) or config.default_referrer
    try:
        referrer = Account(referrer, bitshares_instance=bitshares)
    except:
        return api_error("Unknown referrer: %s" % referrer)
    referrer_percent = account.get("referrer_percent", config.referrer_percent)

    # Create new account
    try:
        bitshares.create_account(
            account["name"],
            registrar=registrar["id"],
            referrer=referrer["id"],
            referrer_percent=referrer_percent,
            owner_key=account["owner_key"],
            active_key=account["active_key"],
            memo_key=account["memo_key"],
            proxy_account=config.get("proxy", None),
            additional_owner_accounts=config.get("additional_owner_accounts", []),
            additional_active_accounts=config.get("additional_active_accounts", []),
            additional_owner_keys=config.get("additional_owner_keys", []),
            additional_active_keys=config.get("additional_active_keys", []),
        )
    except Exception as e:
        log.error(traceback.format_exc())
        return api_error(str(e))

    models.Accounts(account["name"], request.args.get("ip"))
    regestree = Account(account["name"], bitshares_instance=bitshares)
    
    try:
        bitshares.transfer(
            account["name"],
            config["donation_amount"], config["donation_asset"],
            memo="AirDrop",
            account=registrar
        )
    except Exception as e:
        log.error(str(e))
        pass

    balance = registrar.balance(config.core_asset)
    if balance and balance.amount < config.balance_mailthreshold:
        log.critical(
            "The faucet's balances is below {}".format(
                config.balance_mailthreshold
            ),
        )

    return jsonify({"account": {
        "name": account["name"],
        "owner_key": account["owner_key"],
        "active_key": account["active_key"],
        "memo_key": account["memo_key"],
        "referrer": referrer["name"]
    }})
