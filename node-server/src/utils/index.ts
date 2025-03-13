import lodash from 'lodash'

const getDataByField = ({ fields, object }: { fields: Array<string>; object: object }) => {
  return lodash.pick(object, fields)
}

export { getDataByField }
