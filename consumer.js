const kafka = require('kafka-node');

// Kafka client setup
const kafkaClient = new kafka.KafkaClient({ kafkaHost: 'localhost:9092' });

// Consumer setup
const consumer = new kafka.Consumer(
    kafkaClient,
    [{ topic: 'emoji_topic', partition: 0 }], // Topics to subscribe to
    {
        autoCommit: true, // Automatically commit offsets
        fromOffset: false, // Start from the latest message
    }
);

// Event handler for receiving messages
consumer.on('message', (message) => {
    console.log('Received message:', message);

    // Parse and process the message
    try {
        const parsedMessages = JSON.parse(message.value);
        console.log('Parsed messages:', parsedMessages);
    } catch (error) {
        console.error('Error parsing message:', error);
    }
});

// Handle errors
consumer.on('error', (err) => {
    console.error('Error in Kafka consumer:', err);
});

console.log('Kafka consumer is running...');

