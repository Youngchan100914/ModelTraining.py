x1 = int(input("좌변의 x의 계수:"))
num1 = int(input("좌변의 상수항:"))
x2 = int(input("우변의 x의 계수:"))
num2 = int(input("우변의 상수항:"))
num = num2 - num1
x = num / (x1 - x2)
print("%dx + %d = %dx + %d" % (x1, num1, x2, num2))
print("x = ", x)