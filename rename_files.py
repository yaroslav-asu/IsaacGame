import os
input()
for fileName in os.listdir("C:/Python Projects/IsaacGame/assets/enemys/i-blob"):
    print(fileName)

    a = fileName.split('-')[-1].replace('.png', '')
    os.rename(fileName, f'i-blob-{int(a) - 1}.png')
