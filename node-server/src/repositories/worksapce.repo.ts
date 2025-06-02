import Workspace, { WorkspaceModel } from '@/models/workspace.model'
import { FilterQuery } from 'mongoose'
import { UpdateQuery } from 'mongoose'

async function create(workspace: Workspace) {
  return WorkspaceModel.create(workspace)
}

async function findBySlug(slug: string) {
  return WorkspaceModel.findOne({ slug }).lean()
}

async function findByUserId(userId: string) {
  return WorkspaceModel.find({ user: userId }).lean()
}

async function updateOne(filter: FilterQuery<Workspace>, update: UpdateQuery<Workspace>) {
  return WorkspaceModel.updateOne(filter, update)
}

export default {
  create,
  findBySlug,
  findByUserId,
  updateOne
}
