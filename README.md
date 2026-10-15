# Handcrafted Marketplace

Single-app Django + Bootstrap marketplace demo. SQLite, no real payments.

## Windows setup

```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
python manage.py makemigrations handcrafted_app
python manage.py migrate
python manage.py seed_categories
python manage.py createsuperuser
python manage.py runserver
```

Visit http://127.0.0.1:8001/ and http://127.0.0.1:8001/admin/.

Register a seller, then approve the SellerProfile in admin and enable accepts_custom_orders. Register a buyer separately to test cart, checkout and requests.

### Limitations

This is a local demo, not production-ready. No payment gateway, buyer acceptance of custom quotes, shipping integration, or per-seller fulfillment status. Shared orders have a global status managed by admin. Migrations must be generated locally if they are not included. Use environment-based SECRET_KEY and DEBUG=False for deployment. Product photos and reference images are local media files.
