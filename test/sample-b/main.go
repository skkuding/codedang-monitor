// main.go
package main

import (
	"encoding/json"
	"fmt"
	"log"
	"math/rand"
	"time"

	amqp "github.com/rabbitmq/amqp091-go"
)

type Message struct {
	TraceId string      `json:"traceId"`
	From    string      `json:"from"`
	Data    interface{} `json:"data"`
}

func failOnError(err error, msg string) {
	if err != nil {
		log.Panicf("%s: %s", msg, err)
	}
}

func main() {
	conn, err := amqp.Dial("amqp://guest:guest@localhost:5672/")
	failOnError(err, "Failed to connect to RabbitMQ")
	defer conn.Close()

	ch, err := conn.Channel()
	failOnError(err, "Failed to open a channel")
	defer ch.Close()

	err = ch.ExchangeDeclare(
		"trace.exchange", // name
		"topic",          // type
		true,             // durable
		false,            // auto-deleted
		false,            // internal
		false,            // no-wait
		nil,              // arguments
	)
	failOnError(err, "Failed to declare an exchange")

	q, err := ch.QueueDeclare(
		"go.queue", // name
		true,       // durable
		false,      // delete when unused
		false,      // exclusive
		false,      // no-wait
		nil,        // arguments
	)
	failOnError(err, "Failed to declare a queue")

	err = ch.QueueBind(
		q.Name,           // queue name
		"route.go",       // routing key
		"trace.exchange", // exchange
		false,            // no-wait
		nil,              // arguments
	)
	failOnError(err, "Failed to bind a queue")

	msgs, err := ch.Consume(
		q.Name, // queue
		"",     // consumer
		true,   // auto-ack
		false,  // exclusive
		false,  // no-local
		false,  // no-wait
		nil,    // args
	)
	failOnError(err, "Failed to register a consumer")

	forever := make(chan bool)

	go func() {
		for d := range msgs {
			var msg Message
			err := json.Unmarshal(d.Body, &msg)
			if err != nil {
				log.Printf("Error decoding message: %s", err)
				continue
			}

			log.Printf(" [x] Received message: %+v", msg)

			// 간단한 처리 (예: 데이터에 "processed-by-go" 추가)
			processedData := make(map[string]interface{})
			err = json.Unmarshal(d.Body, &processedData)
			if err == nil {
				processedData["processedBy"] = "go-app"
			}

			// 새로운 트레이스 ID 또는 기존 ID 사용
			publishTraceId := msg.TraceId
			if publishTraceId == "" {
				publishTraceId = fmt.Sprintf("%d-%d", time.Now().UnixNano(), rand.Intn(1000))
			}

			publishPayload := Message{
				TraceId: publishTraceId,
				From:    "go-app",
				Data:    processedData,
			}
			publishBody, err := json.Marshal(publishPayload)
			if err != nil {
				log.Printf("Error encoding publish payload: %s", err)
				continue
			}

			err = ch.Publish(
				"trace.exchange", // exchange
				"route.nestjs",   // routing key
				false,            // mandatory
				false,            // immediate
				amqp.Publishing{
					ContentType: "application/json",
					Body:        publishBody,
				})
			failOnError(err, "Failed to publish a message")
			log.Printf(" [y] Published processed message with Trace ID: %s", publishTraceId)
		}
	}()

	log.Printf(" [*] Waiting for messages. To exit press CTRL+C")
	<-forever
}
