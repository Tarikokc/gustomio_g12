import xmlrpc.client

url = "http://192.168.10.106:8069"

db = "gustomio"
username = "admin@gustomio.com"
password = "admin"

common = xmlrpc.client.ServerProxy(
    f"{url}/xmlrpc/2/common"
)

uid = common.authenticate(
    db,
    username,
    password,
    {}
)

print("UID =", uid)


client= resto-italien
produit =burrata