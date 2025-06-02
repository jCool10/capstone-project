import { MessagesModel } from '@/models/message.model'

import { IMessages } from '@/models/message.model'

async function create(message: IMessages) {
  return MessagesModel.create(message)
}

async function findOneAndUpdate(workspaceId: string, question: string, response: string, sourceDocuments: string[]) {
  const query = { workspaceId },
    update = {
      $addToSet: {
        messages: [
          { message: question, type: 'userMessage' },
          { message: response, type: 'apiMessage', sourceDocs: sourceDocuments }
        ]
      }
    },
    options = { new: true, upsert: true }
  return MessagesModel.findOneAndUpdate(query, update, options)
}

async function getMessages(workspaceSlug: string) {
  return MessagesModel.find({ slug: workspaceSlug }).sort({ createdAt: -1 }).lean()
}

export default {
  create,
  findOneAndUpdate,
  getMessages
}
