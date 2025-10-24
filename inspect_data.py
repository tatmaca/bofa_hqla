import duckdb
import matplotlib.pyplot as plt

con = duckdb.connect("./hqlamonitor.duckdb")

# Event counts by source
counts = con.execute("""
    SELECT 'Fed Speeches' AS source, COUNT(*) FROM fed_rss
    UNION ALL
    SELECT 'Treasury Auctions', COUNT(*) FROM treasury_auctions
    UNION ALL
    SELECT 'SEC Releases', COUNT(*) FROM sec_rss
""").fetchdf()

counts.plot(kind="bar", x="source", y="count", legend=False)
plt.title("Monitored Events Captured")
plt.tight_layout()
plt.savefig("events_captured.png")   # <-- saves to file
plt.show()                           # <-- opens interactive window

# Treasury auctions timeline
df = con.execute("""
    SELECT auction_date, offering_amount
    FROM treasury_auctions
    ORDER BY auction_date
""").fetchdf()

plt.figure()
plt.scatter(df["auction_date"], df["offering_amount"])
plt.xticks(rotation=45)
plt.title("Upcoming Treasury Auctions")
plt.ylabel("Offering Amount ($)")
plt.tight_layout()
plt.savefig("treasury_auctions.png")  # <-- saves to file
plt.show()
