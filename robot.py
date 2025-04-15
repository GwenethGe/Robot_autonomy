from pymycobot import MyArmM
import time

myarmm = MyArmM("COM3")

angles = myarmm.get_joints_angle()
print(f"Current joints angles: {angles}")
