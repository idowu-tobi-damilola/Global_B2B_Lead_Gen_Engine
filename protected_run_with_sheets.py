from expiration import check_expiration
if not check_expiration():
    print("🔒 SERVICE EXPIRED")
    exit(0)
exec(open("run_with_sheets.py").read())
