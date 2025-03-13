import winston from 'winston'
import 'winston-daily-rotate-file'

const format = winston.format.combine(
  winston.format.colorize(),
  winston.format.printf(({ level, message, service, origin = '', timestamp }) => {
    const time = timestamp ? `\x1b[90m[${timestamp}]\x1b[0m ` : ''
    const serviceText = service ? `\x1b[36m[${service}]\x1b[0m` : ''
    const originText = origin ? ` \x1b[33m[${origin}]\x1b[0m` : ''
    return `${time}${serviceText}${originText} ${level}: ${message}`
  }),
  winston.format.timestamp()
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
      zippedArchive: true,
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
