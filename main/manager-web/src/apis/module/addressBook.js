import { getServiceUrl } from '../api';
import RequestService from '../httpRequest';

export default {
  /**
   * Get the device address book list
   */
  getAddressBookList(macAddress, callback) {
    RequestService.sendRequest()
      .url(`${getServiceUrl()}/device/address-book/${macAddress}`)
      .method('GET')
      .success((res) => {
        RequestService.clearRequestTime();
        callback(res);
      })
      .networkFail(() => {
        RequestService.reAjaxFun(() => {
          this.getAddressBookList(macAddress, callback);
        });
      }).send();
  },

  /**
   * Update the alias in the device address book
   */
  updateAlias(data, callback) {
    RequestService.sendRequest()
      .url(`${getServiceUrl()}/device/address-book/alias`)
      .method('PUT')
      .data(data)
      .success((res) => {
        RequestService.clearRequestTime();
        callback(res);
      })
      .networkFail(() => {
        RequestService.reAjaxFun(() => {
          this.updateAlias(data, callback);
        });
      }).send();
  },

  /**
   * Update the permission in the device address book
   */
  updatePermission(data, callback) {
    RequestService.sendRequest()
      .url(`${getServiceUrl()}/device/address-book/permission`)
      .method('PUT')
      .data(data)
      .success((res) => {
        RequestService.clearRequestTime();
        callback(res);
      })
      .networkFail(() => {
        RequestService.reAjaxFun(() => {
          this.updatePermission(data, callback);
        });
      }).send();
  }
};