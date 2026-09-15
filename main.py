import json
import os
import smtplib
from email.message import EmailMessage

import requests


URL = "https://www.lg.com/api/graphql"

PRODUCTS = {
    "CV9014BC2.ABLFBRS.ESSP.BR.C": {
        "url": "https://www.lg.com/br/lavanderia/lava-e-seca/cv9014bc2/",
        "threshold": 6000.00,
    },
    "WD18GNTS6B.AEGFBRS.ESSP.BR.C": {
        "url": "https://www.lg.com/br/lavanderia/lava-e-seca/wd18gnts6b/",
        "threshold": 7000.00,
    },
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/153.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Content-Type": "application/json",
    "store": "br",
}


def get_src(sku):
    query = """
    query getProductsBySku(
        $skuList: [String],
        $isSubscription: Boolean = false
    ) {
        products(
            filter: {sku: {in: $skuList}},
            is_subscription: $isSubscription
        ) {
            items {
                name
                sku
                stock_status
                cheaper_price {
                    amount {
                        value
                        currency
                    }
                    cheaper_percent
                }
                price_range {
                    minimum_price {
                        final_price {
                            value
                            currency
                        }
                        regular_price {
                            value
                            currency
                        }
                        discount {
                            amount_off
                            percent_off
                        }
                    }
                }
            }
        }
    }
    """

    params = {
        "query": query,
        "operationName": "getProductsBySku",
        "variables": json.dumps({
            "skuList": [sku],
            "isSubscription": False,
        }),
    }

    response = requests.get(URL, params=params, headers=HEADERS, timeout=15)
    response.raise_for_status()
    payload = response.json()

    if payload.get("errors"):
        raise RuntimeError(f"A API da LG retornou erros: {payload['errors']}")

    return payload


def get_product(sku):
    payload = get_src(sku)
    items = payload.get("data", {}).get("products", {}).get("items", [])
    if not items:
        raise RuntimeError(f"Nenhum produto encontrado para o SKU {sku}")
    return items[0]


def get_price(product):
    amount = product.get("cheaper_price", {}).get("amount", {})
    value = amount.get("value")
    if value is None:
        value = product["price_range"]["minimum_price"]["final_price"]["value"]
    return float(value)


def format_brl(value):
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def send_email(alerts):
    sender = os.environ.get("GMAIL_EMAIL")
    password = os.environ.get("GMAIL_APP_PASSWORD")
    recipient = os.environ.get("ALERT_EMAIL")

    missing = [
        name
        for name, value in {
            "GMAIL_EMAIL": sender,
            "GMAIL_APP_PASSWORD": password,
            "ALERT_EMAIL": recipient,
        }.items()
        if not value
    ]
    if missing:
        raise RuntimeError(
            "Variáveis obrigatórias ausentes para enviar o alerta: "
            + ", ".join(missing)
        )

    lines = ["Um ou mais produtos atingiram o preço desejado na loja LG:\n"]
    for alert in alerts:
        lines.extend([
            f"Produto: {alert['name']}",
            f"Preço atual: {format_brl(alert['price'])}",
            f"Limite: {format_brl(alert['threshold'])}",
            f"Link: {alert['url']}",
            "",
        ])

    message = EmailMessage()
    message["Subject"] = "Alerta de preço LG"
    message["From"] = sender
    message["To"] = recipient
    message.set_content("\n".join(lines))

    with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as smtp:
        smtp.starttls()
        smtp.login(sender, password)
        smtp.send_message(message)

    print(f"E-mail enviado para {recipient}.")


def main():
    alerts = []

    for sku, config in PRODUCTS.items():
        product = get_product(sku)
        price = get_price(product)
        threshold = config["threshold"]

        print(
            f"{product['name']} | {format_brl(price)} | "
            f"limite: {format_brl(threshold)} | {config['url']}"
        )

        if price < threshold:
            alerts.append({
                "name": product["name"],
                "price": price,
                "threshold": threshold,
                "url": config["url"],
            })

    if alerts:
        send_email(alerts)
    else:
        print("Nenhum produto está abaixo do limite configurado.")


if __name__ == "__main__":
    main()
