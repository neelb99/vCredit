from datetime import datetime,timedelta

time = datetime.now() + timedelta(hours=5, minutes=30)
strtime =  time.strftime("%d-%m-%Y at %I:%M %p")

print(strtime)