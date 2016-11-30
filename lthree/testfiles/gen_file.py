f = open('100kb.txt', 'w')

out = ''
count = 0
while len(out) < 100000:
    out += str(count)
    out += ' '
    count += 1

f.write(out)

f.close()