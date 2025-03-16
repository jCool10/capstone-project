import { ReasonPhrases, StatusCodes } from 'http-status-codes'

declare class Error {
  public name: string
  public message: string
  public stack: string
  public status: number
  public isOperational: boolean
  public errors: any
  constructor(message: string)
}

class BaseError extends Error {
  constructor(message: string, status: number, errors: any, isOperational: boolean) {
    super(message)
    this.name = this.constructor.name
    this.status = status
    this.isOperational = isOperational

    Object.setPrototypeOf(this, BaseError.prototype)
  }
}

class NotFoundError extends BaseError {
  constructor(
    message: string = ReasonPhrases.NOT_FOUND,
    errors = [],
    status = StatusCodes.NOT_FOUND,
    isOperational = true
  ) {
    super(message, status, errors, isOperational)
  }
}

class BadRequestError extends BaseError {
  constructor(
    message: string = ReasonPhrases.BAD_REQUEST,
    errors = [],
    status = StatusCodes.BAD_REQUEST,
    isOperational = true
  ) {
    super(message, status, errors, isOperational)
  }
}

class InternalServerError extends BaseError {
  constructor(
    message: string = ReasonPhrases.INTERNAL_SERVER_ERROR,
    errors = [],
    status = StatusCodes.INTERNAL_SERVER_ERROR,
    isOperational = true
  ) {
    super(message, status, errors, isOperational)
  }
}

class UnauthorizedError extends BaseError {
  constructor(
    message: string = ReasonPhrases.UNAUTHORIZED,
    errors = [],
    status = StatusCodes.UNAUTHORIZED,
    isOperational = true
  ) {
    super(message, status, errors, isOperational)
  }
}

class ConflictError extends BaseError {
  constructor(
    message: string = ReasonPhrases.CONFLICT,
    errors = [],
    status = StatusCodes.CONFLICT,
    isOperational = true
  ) {
    super(message, status, errors, isOperational)
  }
}

class ForbiddenError extends BaseError {
  constructor(
    message: string = ReasonPhrases.FORBIDDEN,
    errors = [],
    status = StatusCodes.FORBIDDEN,
    isOperational = true
  ) {
    super(message, status, errors, isOperational)
  }
}

export {
  BaseError,
  NotFoundError,
  BadRequestError,
  InternalServerError,
  UnauthorizedError,
  ConflictError,
  ForbiddenError
}
