import csv
import argparse
import re
import ipaddress


def get_args():
    parser = argparse.ArgumentParser(description='Parse csv with ip and/or network for annotations. Multiple ips per row transposed. Duplicate ip context concatenated.')
    parser.add_argument('-f', dest='file', help='csv file REQUIRED', required=True)
    parser.add_argument('-i', dest='ip', help='ip, network or cidr REQUIRED', required=True)
    parser.add_argument('-m', dest='mask', help='subnet mask or mask length (24 or 255.255.255.0) discarded OPTIONAL', required=False)
    parser.add_argument('-n', dest='new', help='new field combines short and long (if present 40 chars) multiple SHARED REQUIRED', required=False)
    parser.add_argument('-s', dest='short', help='short field (in:out 255 chars) multiple delimited REQUIRED', required=True)
    parser.add_argument('-l', dest='long', help='long field (in:out 255 chars) multiple delimited OPTIONAL', required=False)
    parser.add_argument('-p', dest='parent', help='parent field (in:out 40 chars) multiple SHARED OPTIONAL', required=False)
    parser.add_argument('-d', dest='delimited', help='delimited fields (in:out 255 chars) multiple delimited OPTIONAL', required=False)
    parser.add_argument('-a', dest='add', help='add new field and value (field1=value,field2=value 255 chars) OPTIONAL', required=False)
    parser.add_argument('-k', dest='keep', help='keep fields (in:out 255 chars) retained OPTIONAL', required=False)
    parser.add_argument('-e', dest='exclude', help='values to exclude (field1=value1,value2;field2=value1,value2) discarded OPTIONAL', required=False)
    parser.add_argument('-F', dest='filter', help='filter all but specified values (field1=value1,value2;field2=value1,value2) discarded OPTIONAL', required=False)
    parser.add_argument('-c', dest='case', help='upper/lower/title OPTIONAL', required=False)
    parser.add_argument('-R', dest='regex', help='replace regex with sub (field=regex:sub,regex:sub;field=regex:sub,regex:sub) OPTIONAL special chars [comma] [colon] [equals] [semicolon]', required=False)
    parser.add_argument('-S', dest='search', help='search source for regex and assign value to dest (source=regex:dest=value,source=regex:dest=value) OPTIONAL special chars [comma] [colon] [equals]', required=False)
    parser.add_argument('-V', dest='vlookup', help='lookup key in external file, replace dest with column index (filename:key;index1=dest1,index2=dest2) OPTIONAL', required=False)
    parser.add_argument('-C', dest='combine', help='assign space delimitted fields to dest (dest1=field1,field2,field3;dest2=field4,field5) OPTIONAL', required=False)

    args = parser.parse_args()
    return args


def main():
    args = get_args()

    with open(args.file, encoding='ascii', errors='ignore') as file:
        table = list(csv.reader(file, delimiter=','))

    headers = table.pop(0)
    new_headers = ['IP', args.new]
    output = []
    copies = []
    final = []
    shared = 0
    discarded = 0

    nulls = ['null', 'n/a', 'none', '', '-', 'unknown']

    # get ip index
    if args.ip in headers:
        ip_index = headers.index(args.ip)
    else:
        print(args.ip + ' not found in headers')
        exit()

    # get mask index
    if args.mask is not None:
        if args.mask in headers:
            mask_index = headers.index(args.mask)

            # covert to cidr
            print('\nconverting to cidr')
            for row in table:
                if row[mask_index].lower() not in nulls:
                    if '.' in row[mask_index]:
                        row[ip_index] = str(ipaddress.ip_interface(row[ip_index] + '/' + row[mask_index]).network)
                    else:
                        row[ip_index] = row[ip_index] + '/' + row[mask_index]
        else:
            print(args.mask + ' not found in headers')
            exit()

    # get short index
    if ':' in args.short:
        if args.short.split(':')[0] in headers:
            short_index = headers.index(args.short.split(':')[0])
            new_headers.append(args.short.split(':')[1])
        else:
            print(args.short + ' not found in headers')
            exit()
    else:
        print('short format is in:out')
        exit()

    # get long index
    if args.long is not None:
        if ':' in args.long:
            if args.long.split(':')[0] in headers:
                long_index = headers.index(args.long.split(':')[0])
                new_headers.append(args.long.split(':')[1])
            else:
                print(args.long + ' not found in headers')
                exit()
        else:
            print('long format is in:out')
            exit()

    # get parent index
    if args.parent is not None:
        if ':' in args.parent:
            if args.parent.split(':')[0] in headers:
                parent_index = headers.index(args.parent.split(':')[0])
                new_headers.append(args.parent.split(':')[1])
            else:
                print(args.long + ' not found in headers')
                exit()
        else:
            print('parent format is in:out')
            exit()

    # get delimited indeces
    if args.delimited is not None:
        delimited_indeces = []

        for delimited in args.delimited.split(','):
            if ':' in args.delimited:
                if delimited.split(':')[0] in headers:
                    delimited_indeces.append(headers.index(delimited.split(':')[0]))
                    new_headers.append(delimited.split(':')[1])
                else:
                    print(delimited.split(':')[0] + ' not found in headers')
                    exit()
            else:
                print('delimited format is in:out')
                exit()

    keep_indeces = []

    # get add fields
    if args.add is not None:

        print('\nadding fields')
        for add in args.add.split(','):
            headers.append(add.split('=')[0].strip())
            new_headers.append(add.split('=')[0].strip())
            keep_indeces.append(headers.index(add.split('=')[0].strip()))

            for row in table:
                row.extend([add.split('=')[1].strip()])

    # get keep indeces
    if args.keep is not None:
        for keep in args.keep.split(','):
            if keep.split(':')[0] in headers:
                keep_indeces.append(headers.index(keep.split(':')[0]))
                new_headers.append(keep.split(':')[1])
            else:
                print(keep.split(':')[0] + ' not found in headers')
                exit()

    # get exclude indices and values
    if args.exclude is not None:
        excludes = []
        for exclude in args.exclude.split(';'):
            if exclude.split('=')[0] in headers:
                excludes.append(str(headers.index(exclude.split('=')[0])) + '=' + exclude.split('=')[1])
            else:
                print(exclude.split('=')[0] + ' not found in headers')
                exit()

    # get filter indices and values
    if args.filter is not None:
        filters = []
        for f in args.filter.split(';'):
            if f.split('=')[0] in headers:
                filters.append(str(headers.index(f.split('=')[0])) + '=' + f.split('=')[1])
            else:
                print(f.split('=')[0] + ' not found in headers')
                exit()

    # get regex subs
    if args.regex is not None:
        res = []
        for regex in args.regex.split(';'):
            if regex.split('=')[0] in headers:
                for pair in regex.split('=')[1].split(','):
                    res.append([headers.index(regex.split('=')[0]), pair.split(':')[0], pair.split(':')[1]])
            else:
                print(regex.split('=')[0] + ' not found in headers')
                exit()

        # apply regex subs
        print('\nregex substitution')
        for row in table:
            for regex in res:
                row[regex[0]] = re.sub(regex[1].replace('[colon]', ':').replace('[comma]', ',').replace('[equals]', ',').replace('[semicolon]', ','), regex[2], row[regex[0]])

    # get search
    if args.search is not None:
        res = []
        for regex in args.search.split(','):
            if regex.split('=')[0] in headers and regex.split(':')[1].split('=')[0] in headers:
                res.append([headers.index(regex.split('=')[0]), regex.split(':')[0].split('=')[1], headers.index(regex.split(':')[1].split('=')[0]), regex.split(':')[1].split('=')[1]])
            else:
                print(regex + ' not found in headers')
                exit()

        # apply regex search
        print('\nregex search')
        for row in table:
            for regex in res:
                if re.search(regex[1].replace('[colon]', ':').replace('[comma]', ',').replace('[equals]', ','), row[regex[0]]) is not None:
                    row[regex[2]] = regex[3]

    # get vlookup
    if args.vlookup is not None:
        key = args.vlookup.split(':')[1].split(';')[0]
        key_index = None
        if key in headers:
            key_index = headers.index(key)

            for pair in args.vlookup.split(';')[1].split(','):
                if pair.split(':')[1] not in headers:
                    print('vlookup ' + pair + ' not found in headers')
                    exit()

            print('\nvlookup')
            with open(args.vlookup.split(':')[0], encoding='utf8', errors='ignore') as file:
                lookup_table = list(csv.reader(file, delimiter=','))

            for row in table:
                for record in lookup_table:
                    if row[key_index] == record[0]:
                        for pair in args.vlookup.split(';')[1].split(','):
                            row[headers.index(pair.split(':')[1])] = record[int(pair.split(':')[0])]
                        break
        else:
            print('vlookup ' + key + ' not found in headers')
            exit()

    # get combine indeces
    if args.combine is not None:

        combines = []

        for dest in args.combine.split(';'):
            if dest.split('=')[0] not in headers:
                print('combine dest ' + dest.split('=')[0] + ' not found in headers')
                exit()
            dest_index = headers.index(dest.split('=')[0])
            combine_indeces = []
            for field in dest.split('=')[1].split(','):
                combine_indeces.append(headers.index(field))
            combines.append([dest_index, combine_indeces])
        print('\ncombining')
        for row in table:
            for combine in combines:
                value = ''
                for index in combine[1]:
                    if row[index].strip() != '':
                        value += ' ' + row[index].strip()
                row[combine[0]] = value

    # mutiple ips per row
    print('\ntransposing')
    for row in table:
        #row = [x.strip() for x in row]
        row[ip_index] = row[ip_index].lower().strip()

        if ',' in row[ip_index]:
            ips = row[ip_index].split(',')
            row[ip_index] = ips.pop(0).strip()

            for ip in ips:
                ip = ip.strip()
                if ip not in nulls:
                    copy = row.copy()
                    copy[ip_index] = ip
                    copies.append(copy)

        if ';' in row[ip_index]:
            ips = row[ip_index].split(';')
            row[ip_index] = ips.pop(0).strip()

            for ip in ips:
                ip = ip.strip()
                if ip not in nulls:
                    copy = row.copy()
                    copy[ip_index] = ip
                    copies.append(copy)

        if ' ' in row[ip_index]:
            ips = row[ip_index].split(' ')
            row[ip_index] = ips.pop(0).strip()

            for ip in ips:
                ip = ip.strip()
                if ip not in nulls:
                    copy = row.copy()
                    copy[ip_index] = ip
                    copies.append(copy)

    table = table + copies

    print('\nconcatenating')
    for row in table:
        # filter field
        if args.filter is not None:
            consider = False
            for f in filters:
                if row[int(f.split('=')[0])] in f.split('=')[1].split(','):
                    consider = True
        else:
            consider = True

        # exclude field
        if args.exclude is not None:
            for exclude in excludes:
                if row[int(exclude.split('=')[0])] in exclude.split('=')[1].split(','):
                    consider = False

        if row[ip_index].lower() not in nulls and row[short_index].lower() not in nulls and consider:

            new = True

            # check for dups
            for line in output:
                if line[ip_index] == row[ip_index]:
                    new = False

                    # delimit
                    if row[short_index] not in line[short_index].split('\n'):

                        # long field
                        if args.long is not None:
                            if '=' not in line[long_index]:
                                line[long_index] = line[short_index] + '=' + line[long_index]
                            line[long_index] = row[short_index] + '=' + row[long_index] + '\n' + line[long_index]
                            # line[long_index] = row[short_index] + '=' + row[long_index].split(':')[0] + '\n' + line[long_index]
                            L = line[long_index].split('\n')
                            L.sort()
                            line[long_index] = '\n'.join(L)

                        # delimitted fields
                        if args.delimited is not None:
                            for index in delimited_indeces:
                                if '=' not in line[index]:
                                    line[index] = line[short_index] + '=' + line[index]
                                line[index] = row[short_index] + '=' + row[index] + '\n' + line[index]
                                # line[index] = row[short_index] + '=' + row[index].split(':')[0] + '\n' + line[index]
                                L = line[index].split('\n')
                                L.sort()
                                line[index] = '\n'.join(L)

                        # parent field
                        if args.parent is not None:
                            if row[parent_index] != line[parent_index]:
                                line[parent_index] = 'SHARED'

                        # short field
                        line[short_index] = line[short_index] + '\n' + row[short_index]
                        L = line[short_index].split('\n')
                        L.sort()
                        line[short_index] = '\n'.join(L)

            if new:
                output.append(row)
        else:
            discarded += 1

    print('\nformatting')
    for line in output:
        entry = []

        # ip field
        entry.append(line[ip_index])

        # new application field
        if len(line[short_index].split('\n')) == 1:
            if args.long is not None:
                if line[short_index] != line[long_index].split(' ')[0]:
                    entry.append((line[short_index] + ' ' + line[long_index])[:40])
                else:
                    entry.append(line[long_index][:40])
            else:
                entry.append(line[short_index][:40])
        else:
            shared += 1
            entry.append('SHARED')

        # short field
        entry.append(line[short_index][:255])

        # long field
        if args.long is not None:
            entry.append(line[long_index].split(':')[0][:255])

        # parent field
        if args.parent is not None:
            entry.append(line[parent_index].strip()[:40])

        # delimited fields
        if args.delimited is not None:
            for index in delimited_indeces:
                entry.append(line[index][:255])

        # keep fields
        if args.keep is not None:
            for index in keep_indeces:
                entry.append(line[index].strip()[:255])

        # case
        if args.case is not None:
            if args.case == 'upper':
                entry = [x.upper() for x in entry]
            if args.case == 'lower':
                entry = [x.lower() for x in entry]
            if args.case == 'title':
                entry = [x.title() for x in entry]

        # whitespace
        entry = [x.strip() for x in entry]

        final.append(entry)

    print('\nrows: ' + str(len(table)))
    print('discarded: ' + str(discarded))

    print('\nfinal: ' + str(len(final)))
    print('shared: ' + str(shared))

    final = sorted(final, key=lambda x: x[1])
    final.insert(0, new_headers)
    writer = csv.writer(open('annotations_' + args.file.split('.')[0] + '.csv', 'w', newline=''))
    writer.writerows(final)

    print('\ncreated: annotations_' + args.file.split('.')[0] + '.csv\n')


if __name__ == '__main__':
    main()
