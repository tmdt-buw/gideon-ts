import { registerLocaleData } from '@angular/common';
import { HttpClientModule } from '@angular/common/http';
import en from '@angular/common/locales/en';
import { NgModule } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { BrowserModule } from '@angular/platform-browser';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { RouterModule } from '@angular/router';
import { en_US, NZ_I18N } from 'ng-zorro-antd/i18n';
import { NgxEchartsModule } from 'ngx-echarts';
import { ApiModule, Configuration } from '../api';
import { environment } from '../environments/environment';
import { AppComponent } from './app.component';
import { APP_ROUTES } from './app.routes';
import { SharedModule } from './shared.module';
import { NzProgressModule } from 'ng-zorro-antd/progress';
registerLocaleData(en);

function configFactory(): Configuration {
  return new Configuration({basePath: environment.baseUrl});
}

@NgModule({
  declarations: [
    AppComponent
  ],
  imports: [
    ApiModule.forRoot(configFactory),
    BrowserAnimationsModule,
    BrowserModule,
    FormsModule,
    HttpClientModule,
    SharedModule,
    NgxEchartsModule.forRoot({
      echarts: () => import('echarts')
    }),
    RouterModule.forRoot(APP_ROUTES)
  ],
  providers: [{provide: NZ_I18N, useValue: en_US}],
  bootstrap: [AppComponent]
})
export class AppModule {
}
