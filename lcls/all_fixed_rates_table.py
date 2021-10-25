import argparse

factors = [[1,2,4,8,16],[1,5,25,125,625],[1,7],[1,13]]

def main():
#    parser = argparse.ArgumentParser(description='tabulate all possible fixed rates')
#    args = parser.parse_args()


    result = []
    base = 1300.e6/1400

    factor=0
    rate=1
    for i in factors[0]:
        for j in factors[1]:
            for k in factors[2]:
                for l in factors[3]:
                    f = i*j*k*l
                    result.append({factor:f,rate:base/float(f)})

    print(len(result))

    print('     Rate   SubHarmonic')
    for r in sorted(result, key=lambda entry: entry[rate]):
        print(' {:6.0f} Hz    {:3d}'.format(r[rate],r[factor]))


if __name__=='__main__':
    main()
