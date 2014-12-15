#!/usr/bin/env python3
# encoding: utf-8
from iOSReader import reader, datetime
import matplotlib.pyplot as plt
from clint.textui import progress

r = reader()

# Constants:
prefix = "Sechler"
numlines = 10
numdays = 365*1
pollingnum = 10

r.addAddressBook(prefix + "/AddressBook/AddressBook.sqlitedb")
r.addSMSDatabase(prefix + "/sms/sms.db")
numberwords = []
for number in r.getListOfNumbers():
    count = r.countFromNumber(number)
    numberwords.append((number, count))
sortedlist = sorted(numberwords, key=lambda item: item[1], reverse=True)
sortedlist = sortedlist[:numlines]
numberlist = [i[0] for i in sortedlist]
lastday = r.lastDate()
firstday = lastday - datetime.timedelta(days=numdays)
monthlinenums = []
curMonth = datetime.date(lastday.year, lastday.month, 1)
monthdict = {1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun',
             7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'}
while curMonth > firstday.date():
    monthlinenums.append(((curMonth - firstday.date()).days, curMonth))
    if curMonth.month == 1:
        curMonth = datetime.date(curMonth.year - 1, 12, 1)
    else:
        curMonth = datetime.date(curMonth.year, curMonth.month - 1, 1)
with progress.Bar(expected_size=numdays*numlines+(numdays*numlines)//pollingnum) as bar:
    count = 0
    bar.show(count)
    for number in numberlist:
        xlist = []
        ylist = []
        for i in range(numdays, -1, -1):
            date = lastday - datetime.timedelta(days=i)
            xlist.append(numdays-i)
            total = r.totalOnDate(date, number)
            ylist.append(total)
            count += 1
            bar.show(count)
        plt.plot(xlist, ylist, linewidth=2.0, label=r.getNameFromNumber(number))
    plt.ylabel('Number of Messages')
    plt.xlabel('Days since ' + firstday.isoformat()[:10])
    plt.legend([r.getNameFromNumber(number) for number in numberlist], loc=2)
    for line in monthlinenums:
        plt.axvline(x=line[0], ls='--')
        plt.annotate(monthdict[line[1].month], xy=(line[0] + 5, 15))
    fig = plt.gcf()
    fig.set_size_inches(18.5, 10.5)
    fig.savefig(prefix + 'png.png', dpi=100)
    plt.clf()
    for number in numberlist:
        xlist = []
        ylist = []
        startdate = lastday - datetime.timedelta(days=numdays)
        enddate = startdate + datetime.timedelta(days=pollingnum)
        for i in range(numdays//pollingnum, -1, -1):
            endtotal = r.totalOnDate(enddate, number)
            begtotal = r.totalOnDate(startdate, number)
            difference = endtotal - begtotal
            xlist.append(numdays//pollingnum - i)
            ylist.append(difference // pollingnum)
            startdate += datetime.timedelta(days=pollingnum)
            enddate += datetime.timedelta(days=pollingnum)
            count += 1
            bar.show(count)
        plt.plot(xlist, ylist, linewidth=2.0, label=r.getNameFromNumber(number))
    plt.ylabel('Number of Messages per day, {} day polling'.format(pollingnum))
    plt.xlabel('{} Day periods since {}'.format(pollingnum, firstday.isoformat()[:10]))
    plt.legend([r.getNameFromNumber(number) for number in numberlist], loc=2)
    for line in monthlinenums:
        plt.axvline(x=line[0]/pollingnum, ls='--')
        plt.annotate(monthdict[line[1].month], xy=(line[0]/pollingnum + 5/pollingnum, 15))
    fig = plt.gcf()
    fig.set_size_inches(18.5, 10.5)
    fig.savefig(prefix + 'slopes.png', dpi=100)
