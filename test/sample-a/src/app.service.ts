import { AmqpConnection } from '@golevelup/nestjs-rabbitmq';
import { Injectable } from '@nestjs/common';

@Injectable()
export class AppService {
  constructor(private readonly amqpConnection: AmqpConnection) {}

  getHello(): string {
    return 'Hello World!';
  }

  async sendMessage(message: any) {
    const traceId = Math.random().toString(36).substring(2, 15); // 간단한 트레이스 ID 생성
    const payload = { ...message, traceId, from: 'nestjs-producer' };
    await this.amqpConnection.publish('trace.exchange', 'route.go', payload);
    return { message: 'Message sent', traceId };
  }
}
