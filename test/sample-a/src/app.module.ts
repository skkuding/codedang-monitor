import { RabbitMQModule } from '@golevelup/nestjs-rabbitmq';
import { Module } from '@nestjs/common';
import { AppController } from './app.controller';
import { AppService } from './app.service';

@Module({
  imports: [
    RabbitMQModule.forRoot({
      exchanges: [
        {
          name: 'trace.exchange',
          type: 'topic',
        },
      ],
      queues: [
        {
          name: 'nestjs.queue',
        },
      ],
      uri: process.env.RABBITMQ_URI as string, // RabbitMQ 연결 URI
    }),
  ],
  controllers: [AppController],
  providers: [AppService],
})
export class AppModule {}
