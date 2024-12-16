from kafka.admin import KafkaAdminClient, NewTopic
from kafka import KafkaConsumer

bootstrap_servers = ['kafka-broker-1:9092', 'kafka-broker-2:9092', 'kafka-broker-3:9092']

topic_list = ['to-alert-system', 'to-notifier']

num_partitions = 1  
replication_factor = 3  


def create_topic_if_not_exists(topic_list, num_partitions, replication_factor):
    admin_client = KafkaAdminClient(bootstrap_servers=bootstrap_servers, client_id='kafka-admin')
    consumer = KafkaConsumer(bootstrap_servers=bootstrap_servers) # serve per vedere i topic 
    
    for topic in topic_list: 
        if topic not in consumer.topics():
            # creiamolo
            new_topic = NewTopic(
                name=topic,
                num_partitions=num_partitions,
                replication_factor=replication_factor
            )
            try:
                print(f"\nCreazione del topic '{topic}'...")
                admin_client.create_topics(new_topics=[new_topic], validate_only=False)
                print(f"Topic '{topic}' creato con successo, numero partizioni:{num_partitions} e fattore di replica:{replication_factor}.")
            except Exception as e:
                print(f"Si è verificato un errore durante la creazione del topic, codice di errore: {e}")
            finally:
                consumer.close()
                admin_client.close()
        else:
            print(f"\nIl Topic '{topic}' esiste già.")

    consumer.close()
    admin_client.close()


def list_topics_and_details():
    """ Stampa a video la lista dei topic e dei dettagli """
    consumer = KafkaConsumer(bootstrap_servers=bootstrap_servers)
    topics = consumer.topics()  
    print("\nDettagli dei topic disponibili:")

    for topic in sorted(topics):
        partitions = consumer.partitions_for_topic(topic)
        if partitions:
            print(f"\nTopic: {topic}")
            print(f"  Numero partizioni: {len(partitions)}")
            print("  Dettagli sulle partizioni:")
            for partition in sorted(partitions):
                print(f"    Partizione {partition}")
        else:
            print(f"\nTopic: {topic}")
            print("  Non ci sono partizioni disponibili per questo topic.")

    consumer.close()