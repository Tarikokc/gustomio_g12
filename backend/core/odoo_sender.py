# import xmlrpc.client

# ODOO_URL      = "http://192.168.10.106:8069"
# ODOO_DB       = "gustomio"
# ODOO_USER     = "admin@gustomio.com"
# ODOO_PASSWORD = "admin"

# def get_odoo_connection():
#     common = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/common")
#     uid = common.authenticate(ODOO_DB, ODOO_USER, ODOO_PASSWORD, {})
#     models = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/object")
#     return uid, models

# def get_or_create_partner(models, uid, partner_name: str) -> int:
#     results = models.execute_kw(
#         ODOO_DB, uid, ODOO_PASSWORD,
#         "res.partner", "search_read",
#         [[["name", "ilike", partner_name]]],
#         {"fields": ["id", "name"], "limit": 1}
#     )
#     if results:
#         print(f"✅ Fournisseur trouvé : {results[0]['name']}")
#         return results[0]["id"]
#     partner_id = models.execute_kw(
#         ODOO_DB, uid, ODOO_PASSWORD,
#         "res.partner", "create",
#         [{"name": partner_name, "supplier_rank": 1}]
#     )
#     print(f"➕ Fournisseur créé : {partner_name} (ID: {partner_id})")
#     return partner_id

# def get_or_create_product(models, uid, product_name: str) -> int:
#     results = models.execute_kw(
#         ODOO_DB, uid, ODOO_PASSWORD,
#         "product.product", "search_read",
#         [[["name", "ilike", product_name]]],
#         {"fields": ["id", "name"], "limit": 1}
#     )
#     if results:
#         print(f"✅ Produit trouvé : {results[0]['name']}")
#         return results[0]["id"]
#     tmpl_id = models.execute_kw(
#         ODOO_DB, uid, ODOO_PASSWORD,
#         "product.template", "create",
#         [{"name": product_name, "type": "consu", "purchase_ok": True, "sale_ok": False}]
#     )
#     variants = models.execute_kw(
#         ODOO_DB, uid, ODOO_PASSWORD,
#         "product.product", "search_read",
#         [[["product_tmpl_id", "=", tmpl_id]]],
#         {"fields": ["id"], "limit": 1}
#     )
#     product_id = variants[0]["id"]
#     print(f"➕ Produit créé : {product_name} (ID: {product_id})")
#     return product_id

# def send_order_to_odoo(order) -> int | None:
#     uid, models = get_odoo_connection()

#     # Fournisseur
#     partner_id = None
#     if order.customer_name:
#         partner_id = get_or_create_partner(models, uid, order.customer_name)

#     # Lignes de commande
#     order_lines = []
#     for line in order.lines:
#         if line.quantite is None:
#             print(f"⚠️ Quantité manquante pour '{line.produit}', ligne ignorée")
#             continue
#         product_id = get_or_create_product(models, uid, line.produit)
#         order_lines.append([0, 0, {
#             "product_id": product_id,
#             "product_qty": float(line.quantite),
#             "price_unit": 0.0,
#         }])

#     if not order_lines:
#         print("❌ Aucune ligne valide à envoyer à Odoo")
#         return None

#     # Création commande — seulement les champs essentiels
#     order_data = {"order_line": order_lines}
#     if partner_id:
#         order_data["partner_id"] = partner_id

#     order_id = models.execute_kw(
#         ODOO_DB, uid, ODOO_PASSWORD,
#         "purchase.order", "create",
#         [order_data]
#     )
#     print(f"✅ Commande créée dans Odoo — ID : {order_id}")
#     return order_id

import xmlrpc.client

ODOO_URL      = "http://192.168.10.106:8069"
ODOO_DB       = "gustomio"
ODOO_USER     = "admin@gustomio.com"
ODOO_PASSWORD = "admin"

def get_odoo_connection():
    common = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/common")
    uid = common.authenticate(ODOO_DB, ODOO_USER, ODOO_PASSWORD, {})
    models = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/object")
    return uid, models

def get_or_create_partner(models, uid, partner_name: str) -> int:
    results = models.execute_kw(
        ODOO_DB, uid, ODOO_PASSWORD,
        "res.partner", "search_read",
        [[["name", "ilike", partner_name]]],
        {"fields": ["id", "name"], "limit": 1}
    )
    if results:
        print(f"✅ Client trouvé : {results[0]['name']}")
        return results[0]["id"]
    partner_id = models.execute_kw(
        ODOO_DB, uid, ODOO_PASSWORD,
        "res.partner", "create",
        [{"name": partner_name, "customer_rank": 1}]
    )
    print(f"➕ Client créé : {partner_name} (ID: {partner_id})")
    return partner_id

def get_or_create_product(models, uid, product_name: str) -> int:
    results = models.execute_kw(
        ODOO_DB, uid, ODOO_PASSWORD,
        "product.product", "search_read",
        [[["name", "ilike", product_name]]],
        {"fields": ["id", "name"], "limit": 1}
    )
    if results:
        print(f"✅ Produit trouvé : {results[0]['name']}")
        return results[0]["id"]
    tmpl_id = models.execute_kw(
        ODOO_DB, uid, ODOO_PASSWORD,
        "product.template", "create",
        [{"name": product_name, "type": "consu", "sale_ok": True, "purchase_ok": False}]
    )
    variants = models.execute_kw(
        ODOO_DB, uid, ODOO_PASSWORD,
        "product.product", "search_read",
        [[["product_tmpl_id", "=", tmpl_id]]],
        {"fields": ["id"], "limit": 1}
    )
    product_id = variants[0]["id"]
    print(f"➕ Produit créé : {product_name} (ID: {product_id})")
    return product_id

def send_order_to_odoo(order) -> int | None:
    uid, models = get_odoo_connection()

    # Client
    partner_id = None
    if order.customer_name:
        partner_id = get_or_create_partner(models, uid, order.customer_name)

    # Lignes de commande (sale.order.line)
    order_lines = []
    for line in order.lines:
        if line.quantite is None:
            print(f"⚠️ Quantité manquante pour '{line.produit}', ligne ignorée")
            continue
        product_id = get_or_create_product(models, uid, line.produit)
        order_lines.append([0, 0, {
            "product_id": product_id,
            "product_uom_qty": float(line.quantite),
            "price_unit": 0.0,
        }])

    if not order_lines:
        print("❌ Aucune ligne valide à envoyer à Odoo")
        return None

    # Création commande vente (sale.order)
    order_data = {"order_line": order_lines}
    if partner_id:
        order_data["partner_id"] = partner_id

    order_id = models.execute_kw(
        ODOO_DB, uid, ODOO_PASSWORD,
        "sale.order", "create",
        [order_data]
    )
    print(f"✅ Commande vente créée dans Odoo — ID : {order_id}")
    return order_id