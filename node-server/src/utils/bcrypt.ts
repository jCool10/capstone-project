import bcrypt from 'bcrypt'

const comparePassword = async (password: string, hash: string) => {
  return bcrypt.compare(password, hash)
}

const hashPassword = async (password: string) => {
  const salt = await bcrypt.genSalt(10)
  return bcrypt.hash(password, salt)
}

export { comparePassword, hashPassword }
