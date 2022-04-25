import { Injectable } from '@angular/core';
import { webSocket, WebSocketSubject } from 'rxjs/webSocket';
import { environment } from '../../environments/environment';


@Injectable({
  providedIn: 'root'
})
export class WebSocketService {

  readonly WS_ENDPOINT = environment.websocket.url;

  private socket$: WebSocketSubject<any>;

  constructor() {}

  public connect(): WebSocketSubject<any> {
    if (!this.socket$ || this.socket$.closed) {
      this.socket$ = webSocket(this.WS_ENDPOINT);
    }
    return this.socket$;
  }

  closeConnection() {
    this.connect().complete();
  }

}
