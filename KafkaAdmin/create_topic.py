from confluent_kafka.admin import AdminClient, NewTopic

bootstrap_servers = ["kafka-broker-1:9092" ,"kafka-broker-2:9092" ,"kafka-broker-3:9092"]

conf = {
    'bootstrap.servers': "kafka-broker-1:9092,kafka-broker-2:9092,kafka-broker-3:9092"
}

topics_to_create = ['to-alert-system', 'to-notifier']
num_partitions = 1  
replication_factor = 3  


def create_topic_if_not_exists(topics_to_create, num_partitions, replication_factor):
    try:    
        admin_client = AdminClient(conf)
        cluster_metadata = admin_client.list_topics(timeout=10)
        topics = cluster_metadata.topics
        for topic in topics_to_create: 
            if topic not in topics:
                # provvediamo a crearlo
                new_topic = NewTopic(
                    topic=topic,
                    num_partitions=num_partitions,
                    replication_factor=replication_factor
                )

                # Richiesta di creazione
                futures = admin_client.create_topics(new_topics=[new_topic])
                for topic_name, future in futures.items():
                    try:
                        future.result()  # Attende il completamento della creazione
                        print(f"Topic '{topic_name}' creato con successo.")
                    except Exception as e:
                        print(f"Errore durante la creazione del topic '{topic}': {e}") 
                        admin_client.close()         

    except Exception as e:
        print(f"Errore durante il recupero dei topic: codice errore: {e}")


def list_topics_and_details():
    try:
        admin_client = AdminClient(conf)
        cluster_metadata = admin_client.list_topics(timeout=10)
        topics = cluster_metadata.topics

        print("\nDettagli dei topic disponibili:")
        
        for topic_name, topic_metadata in topics.items():
            print(f"\nTopic: {topic_name}")
            print(f"  Numero di partizioni: {len(topic_metadata.partitions)}")
            
            for partition_id, partition_metadata in topic_metadata.partitions.items():
                leader = partition_metadata.leader  # Broker leader della partizione
                replicas = partition_metadata.replicas  # Lista dei replica broker
                isrs = partition_metadata.isrs  # Lista degli ISR (replica in sync)

                print(f"    Partizione {partition_id}:")
                print(f"      Leader: {leader}")
                print(f"      Repliche: {replicas}")
                print(f"      ISR: {isrs}")


    except Exception as e:
         print(f"Errore durante il recupero dei topic: codice errore: {e}")