import { MessagesModel } from '@/models/message.model'

import { IMessages } from '@/models/message.model'

async function create(message: IMessages) {
  return MessagesModel.create(message)
}

async function findOneAndUpdate(workspaceSlug: string, question: string, response: string, sourceDocuments: string[]) {
  const query = { workspaceSlug },
    update = {
      $push: {
        messages: {
          $each: [
            { message: question, type: 'userMessage' },
            { message: response, type: 'apiMessage', sourceDocs: sourceDocuments }
          ]
        }
      }
    },
    options = { new: true, upsert: true }
  return MessagesModel.findOneAndUpdate(query, update, options)
}

async function getMessages(workspaceSlug: string, limit: number = 10) {
  return MessagesModel.find({ workspaceSlug: workspaceSlug }).sort({ createdAt: -1 }).limit(limit).lean()
}

export default {
  create,
  findOneAndUpdate,
  getMessages
}
