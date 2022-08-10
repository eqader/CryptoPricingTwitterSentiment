import csv
from datetime import datetime,timedelta


file_map={"avalanche.csv":("Avalanchefinal.csv","avalanche-2.csv"),
"binancecoin.csv":("BNBfinal.csv","binancecoin.csv"),
"bitcoin.csv":("Bitcoinfinal.csv","bitcoin.csv"),
"cardano.csv":("Cardanofinal.csv","cardano.csv"),
"dogecoin.csv":("Dogefinal.csv","dogecoin.csv"),
"ethereum.csv":("Ethereumfinal.csv","ethereum.csv"),
"polkadot.csv":("PolkaDotfinal.csv","polkadot.csv"),
"ripple.csv":("XRPfinal.csv","ripple.csv"),
"solana.csv":("Solanafinal.csv","solana.csv"),
"terra-luna.csv":("Terrafinal.csv","terra-luna.csv")}

for out_file in file_map:
    headers=[]
    sent_in={}
    price_in={}
    with open("coin_price/"+file_map[out_file][1]) as csvfile:
        reader=csv.reader(csvfile)
        headers+=reader.__next__()[0:2]
        for row in reader:
            price_in[row[0]]=row[1:2]
    with open("sentiment_output/"+file_map[out_file][0]) as csvfile:
        reader=csv.reader(csvfile)
        headers+=reader.__next__()[1:-1]
        for row in reader:
            sent_in[row[0]]=row[1:]




    with open("agg_output/"+out_file,"w") as csvfile:
        writer=csv.writer(csvfile)
        writer.writerow(headers)
        start_date=datetime(2021,9,1)
        end_date=datetime(2022,3,1)
        current_date=start_date
        while current_date<end_date:
            date_string=current_date.strftime("%Y-%m-%d")
            if date_string in price_in.keys():
                price_data=price_in[date_string]
            else:
                price_data=[""]
                print(f'{out_file}: No price data for {date_string}')
            if date_string in sent_in.keys():
                sent_data=sent_in[date_string]
            else:
                sent_data=[]
                print(f'{out_file}: No sentiment data for {date_string}')
            out=[date_string]+price_data+sent_data
            writer.writerow(out)
                    
            current_date+=timedelta(1)

    
