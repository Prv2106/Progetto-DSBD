from confluent_kafka.admin import AdminClient
from confluent_kafka import KafkaException
import create_topic as ct


def get_metadata():
    try:
        admin_client = AdminClient(ct.conf)
        metadata = admin_client.list_topics(timeout=10)
        
        print("\nBrokers:")
        for broker in metadata.brokers.values():
            print(f"  Broker ID: {broker.id}, Host: {broker.host}, Porta: {broker.port}")

        print("\nTopic e Partizioni:")
        for topic, topic_metadata in metadata.topics.items():
            print(f"  Topic: {topic}")
            if topic_metadata.error:
                print(f"    Errore, codice di errore: {topic_metadata.error}")
            else:
                for partition_id, partition_metadata in topic_metadata.partitions.items():
                    leader = partition_metadata.leader
                    replicas = partition_metadata.replicas
                    isrs = partition_metadata.isrs
                    print(f"    Partizione {partition_id}:")
                    print(f"      Leader: Broker {leader}")
                    print(f"      Repliche: {replicas}")
                    print(f"      Repliche In-Sync (ISR): {isrs}")

    except KafkaException as e:
        print(f"Errore durante il recupero dei metadati, codice di errore: {e}")


if __name__ == "__main__":
    print("Creazione dei topic (se non esistenti...)\n")
    ct.create_topic_if_not_exists(ct.topics_to_create, ct.num_partitions, ct.replication_factor)
    print("Stampa dei dettagli dei topic...")
    ct.list_topics_and_details()

    while True:
        print("Recupero dei metadati...")
        get_metadata()
