from pyspark.sql import SparkSession
from pyspark.sql.functions import window, col, unix_timestamp 
from pyspark.sql.types import TimestampType
from kafka import KafkaProducer
import json

# Step 1: Initialize Spark session
spark = SparkSession.builder.appName("EmojiReactionAggregator").getOrCreate()
spark.sparkContext.setLogLevel("ERROR")

# Step 2: Read the JSON file
file_path = '/home/pes2ug22cs638/BD_PRJ/emoji_data.json'
df = spark.read.option("multiline", "true").json(file_path)

# Step 3: Clean DataFrame (handle corrupt records)
if '_corrupt_record' in df.columns:
    df = df.filter(col("_corrupt_record").isNull()).drop("_corrupt_record")

# Step 4: Convert timestamp string to TimestampType
df = df.withColumn("timestamp", unix_timestamp("timestamp", "yyyy-MM-dd HH:mm:ss").cast(TimestampType()))

# Step 5: Aggregate emoji counts in 2-second intervals
emoji_counts = df.groupBy(
    window(col("timestamp"), "2 seconds").alias("time_window"),
    col("emoji_type")
).count()

# Step 6: Filter emojis with a count greater than 10
filtered_emojis = emoji_counts.filter(col("count") > 10)

# Step 7: Function to send data to Kafka
def send_to_kafka_partition(partition):
    """Initialize Kafka producer and send data for each partition."""
    producer = KafkaProducer(
        bootstrap_servers='localhost:9092',
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    for row in partition:
        result = {
            "window_start": row["time_window"].start.isoformat(),
            "window_end": row["time_window"].end.isoformat(),
            "emoji_type": row["emoji_type"],
            "count": row["count"]
        }
        producer.send('processed_emoji_data', result)
        print(f"Sent to Kafka: {result}")
    producer.close()

# Step 8: Use `foreachPartition` to send data
filtered_emojis.foreachPartition(send_to_kafka_partition)

# Step 9: Stop the Spark session
spark.stop()

