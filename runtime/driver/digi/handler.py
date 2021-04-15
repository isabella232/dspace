import on

"""Mock lamp sets power and brightness to intents."""


@on.control("power")
def h0(p):
    p["status"] = p.get("intent",
                        p.get("status", "undef"))


@on.control("brightness")
def h1(b):
    b["status"] = b.get("intent",
                        b.get("status", "-1"))
