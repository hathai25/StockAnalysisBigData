from pyspark.sql import SparkSession
import logging

def total_volume_per_ticker(dataframe):
    total_volume = dataframe.groupBy('ticker').sum('volume')
    return total_volume

if __name__ == "__main__":
    spark = SparkSession.builder.appName("ReadFromHadoop").getOrCreate()
    spark.sparkContext.setLogLevel("ERROR")

    print("runned")
    input_path = "hdfs://namenode:8020/user/root/kafka_data"
    hadoop_data = spark.read.json(input_path)

    hadoop_data.show()

    total_volume = total_volume_per_ticker(hadoop_data)
    total_volume.show()

    try:
        total_volume.write.format("org.elasticsearch.spark.sql") \
            .option("es.nodes", "https://big-data.es.asia-southeast1.gcp.elastic-cloud.com") \
            .option("es.port", "9243") \
            .option("es.resource", "vn_30") \
            .option("es.net.http.auth.user", "elastic") \
            .option("es.net.http.auth.pass", "Fqlvu8CGw9jIGdxSsSSR4R1z") \
            .option("es.nodes.wan.only", "true") \
            .mode("overwrite") \
            .save()
        logging.info("Dữ liệu đã được gửi thành công lên Elasticsearch!")
    except Exception as e:
        logging.error("Đã xảy ra lỗi khi gửi dữ liệu lên Elasticsearch: %s", str(e))

    spark.stop()
