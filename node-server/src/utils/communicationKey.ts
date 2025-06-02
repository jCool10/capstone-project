import crypto from 'crypto'
import fs from 'fs'
import path from 'path'
const keyPath =
  process.env.NODE_ENV === 'development'
    ? path.resolve(__dirname, `../../storage/comkey`)
    : path.resolve(process.env.STORAGE_DIR ?? path.resolve(__dirname, `../../storage`), `comkey`)

class CommunicationKey {
  #privKeyName = 'ipc-priv.pem'
  #pubKeyName = 'ipc-pub.pem'
  #storageLoc = keyPath

  constructor(generate = false) {
    if (generate) this.#generate()
  }

  get publicKey() {
    return fs.readFileSync(path.resolve(this.#storageLoc, this.#pubKeyName)).toString()
  }

  get privateKey() {
    return fs.readFileSync(path.resolve(this.#storageLoc, this.#privKeyName)).toString()
  }

  #readPrivateKey() {
    return fs.readFileSync(path.resolve(this.#storageLoc, this.#privKeyName))
  }

  #generate() {
    const keyPair = crypto.generateKeyPairSync('rsa', {
      modulusLength: 2048,
      publicKeyEncoding: {
        type: 'pkcs1',
        format: 'pem'
      },
      privateKeyEncoding: {
        type: 'pkcs1',
        format: 'pem'
      }
    })

    if (!fs.existsSync(this.#storageLoc)) fs.mkdirSync(this.#storageLoc, { recursive: true })
    fs.writeFileSync(`${path.resolve(this.#storageLoc, this.#privKeyName)}`, keyPair.privateKey)
    fs.writeFileSync(`${path.resolve(this.#storageLoc, this.#pubKeyName)}`, keyPair.publicKey)
    console.log('RSA key pair generated for signed payloads within AnythingLLM services.')
  }

  // This instance of ComKey on server is intended for generation of Priv/Pub key for signing and decoding.
  // this resource is shared with /collector/ via a class of the same name in /utils which does decoding/verification only
  // while this server class only does signing with the private key.
  sign(textData = '') {
    return crypto.sign('RSA-SHA256', Buffer.from(textData), this.#readPrivateKey()).toString('hex')
  }

  // Use the rolling priv-key to encrypt arbitrary data that is text
  // returns the encrypted content as a base64 string.
  encrypt(textData = '') {
    return crypto.privateEncrypt(this.#readPrivateKey(), Buffer.from(textData, 'utf-8')).toString('base64')
  }
}

export default CommunicationKey
