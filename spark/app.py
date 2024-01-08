from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, explode
from pyspark.sql.types import StringType, StructType, StructField, IntegerType, ArrayType
import subprocess
import threading
import logging


def jobVN30Data(spark):
    json_schema = ArrayType(StructType([
        StructField("time", StringType(), True),
        StructField("open", IntegerType(), True),
        StructField("high", IntegerType(), True),
        StructField("low", IntegerType(), True),
        StructField("close", IntegerType(), True),
        StructField("volume", IntegerType(), True),
        StructField("ticker", StringType(), True)
    ]))

    # Định nghĩa tham số Kafka
    kafka_params = {
        "kafka.bootstrap.servers": "kafka:9092",
        "subscribe": "vn30",
        "startingOffsets": "latest",
        "failOnDataLoss": "false"
    }

    # Đọc dữ liệu từ Kafka
    kafka_df = spark.readStream.format("kafka").options(**kafka_params).load()

    print("Data vn30")
    print(kafka_df)

    # Chuyển đổi cột 'value' từ dạng binary sang chuỗi JSON
    kafka_df = kafka_df.selectExpr("CAST(value AS STRING)")

    stock_df = kafka_df.select(from_json(col("value"), json_schema).alias("data"))

    # Sử dụng hàm explode để biến đổi mảng thành các hàng
    stock_df = stock_df.select(explode(col("data")).alias("stock_data")).select("stock_data.*")

    # Định nghĩa đường dẫn xuất HDFS
    output_path = "hdfs://namenode:8020/user/root/kafka_data"

    # Chỉ định vị trí checkpoint
    checkpoint_location_hdfs = "hdfs://namenode:8020/user/root/checkpoints_hdfs"
    # checkpoint_location_es = "hdfs://namenode:8020/user/root/checkpoints_es"
    # Ghi dữ liệu vào HDFS dưới dạng file parquet
    hdfs_query = stock_df.writeStream \
        .outputMode("append") \
        .format("json") \
        .option("path", output_path) \
        .option("checkpointLocation", checkpoint_location_hdfs) \
        .start()
    
    hdfs_query.awaitTermination()

    # run file hadoop_to_spark.py
    subprocess.run(["python3", "hadoop_to_elastic.py"])

def jobStockRealtimeData(spark):
    json_schema = ArrayType(StructType([
        StructField("time", StringType(), True),
        StructField("open", IntegerType(), True),
        StructField("high", IntegerType(), True),
        StructField("low", IntegerType(), True),
        StructField("close", IntegerType(), True),
        StructField("volume", IntegerType(), True),
        StructField("ticker", StringType(), True)
    ]))

    # Định nghĩa tham số Kafka
    kafka_params = {
        "kafka.bootstrap.servers": "kafka:9092",
        "subscribe": "stock_realtime",
        "startingOffsets": "latest"
    }

    # Đọc dữ liệu từ Kafka
    kafka_df = spark.readStream.format("kafka").options(**kafka_params).load()

    print("Data stock")
    print(kafka_df)

    # Chuyển đổi cột 'value' từ dạng binary sang chuỗi JSON
    # kafka_df = kafka_df.selectExpr("CAST(value AS STRING)")

    # stock_df = kafka_df.select(from_json(col("value"), json_schema).alias("data"))

    # Sử dụng hàm explode để biến đổi mảng thành các hàng
    # stock_df = stock_df.select(explode(col("data")).alias("stock_data")).select("stock_data.*")

    # try:
    #     stock_df.write.format("org.elasticsearch.spark.sql") \
    #         .option("es.nodes", "https://big-data.es.asia-southeast1.gcp.elastic-cloud.com") \
    #         .option("es.port", "9243") \
    #         .option("es.resource", "vn_30") \
    #         .option("es.net.http.auth.user", "elastic") \
    #         .option("es.net.http.auth.pass", "Fqlvu8CGw9jIGdxSsSSR4R1z") \
    #         .option("es.nodes.wan.only", "true") \
    #         .mode("overwrite") \
    #         .save()
    #     logging.info("Dữ liệu đã được gửi thành công lên Elasticsearch!")
    # except Exception as e:
    #     logging.error("Đã xảy ra lỗi khi gửi dữ liệu lên Elasticsearch: %s", str(e))

    
    

if __name__ == "__main__":
    print("Hello")
    # Khởi tạo SparkSession
    spark = SparkSession.builder.appName("KafkaToElasticsearch").getOrCreate()
    spark.sparkContext.setLogLevel("ERROR")

    t1 = threading.Thread(target=jobVN30Data, args=(spark,))
    t2 = threading.Thread(target=jobStockRealtimeData, args=(spark,))
    t1.start()
    t2.start()

    t1.join()
    t2.join()
