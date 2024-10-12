msg = input("msg:" )

message = msg.replace('"', '\\\\"').replace("'", "\\\\'")

print(message)