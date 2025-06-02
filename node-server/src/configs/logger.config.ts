import winston from 'winston'
import 'winston-daily-rotate-file'

const format = winston.format.combine(
  winston.format.timestamp({
    format: 'YYYY-MM-DD HH:mm:ss'
  }),
  winston.format.printf((info) => {
    const { level, message, service, origin = '', timestamp } = info
    const time = timestamp ? `[${timestamp}]` : ''
    const serviceText = service ? `[${service}]` : ''
    const originText = origin ? `[${origin}]` : ''
    return `${time}${serviceText}${originText} ${level}: ${message}`
  })
)

const logger = winston.createLogger({
  level: process.env.NODE_ENV === 'production' ? 'info' : 'debug',
  defaultMeta: { service: 'backend' },
  transports: [
    new winston.transports.Console({
      format: format
    }),
    new winston.transports.DailyRotateFile({
      filename: `./logs/backend-%DATE%.log`,
      datePattern: 'YYYY-MM-DD-HH',
      maxSize: '20m',
      maxFiles: '14d',
      format: format
    }),
    new winston.transports.File({
      filename: './logs/error.log',
      level: 'error',
      format: format
    }),
    new winston.transports.File({
      filename: './logs/combined.log',
      format: format
    })
  ]
})

export default logger
