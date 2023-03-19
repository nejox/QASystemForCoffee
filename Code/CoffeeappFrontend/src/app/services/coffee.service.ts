import {Injectable} from '@angular/core';
import {HttpClient} from '@angular/common/http';
import {BehaviorSubject, delay, map, of, tap} from 'rxjs';

interface ManufacturersWithProducts {
  [manufacturer: string]: string[];
}

export interface AnswerObject {
  extracted_answers: string[];
  generation: string;
}

@Injectable({
  providedIn: 'root',
})
export class CoffeeService {
  private productsSubject =
    new BehaviorSubject<ManufacturersWithProducts | null>(null);
  products$ = this.productsSubject.asObservable();

  manufacturers$ = this.products$.pipe(
    map((products) => (products ? Object.keys(products) : []))
  );

  private currentAnswersSubject = new BehaviorSubject<AnswerObject | null>(null);
  currentAnswers$ = this.currentAnswersSubject.asObservable();

  constructor(private http: HttpClient) {
  }

  getProductsForAllManufacturer() {
    // some Mock data for testing
    // return of({
    //   'delongi': [
    //     'aex321',
    //     'aex2',
    //     'aex3',
    //     'aex4',
    //     'aex5',
    //   ],
    //   'philips': [
    //     'aex1',
    //     'aex2',
    //     'aex3',
    //     'aex4',
    //     'aex5',
    //   ],
    // }).pipe(
    //   delay(1000),
    //   tap((productsResponse) => {
    //     this.productsSubject.next(productsResponse);
    //   })
    // );

    return this.http
      .get<ManufacturersWithProducts>(
        `http://127.0.0.1:8000/getProductsForAllManufacturer/`
      )
      .pipe(
        tap((productsResponse) => {
          this.productsSubject.next(productsResponse);
        })
      );
  }

  getPredictedAnswers({
                        manufacturer,
                        product,
                        question,
                      }: {
    manufacturer: string;
    product: string;
    question: string;
  }) {
    // some Mock data for testing
  //   return of({
  //     extracted_answers:
  //     [
  //     ' fdujeanudinwa undwhd uwnb duwnudhnwudhnwu bndüuwAN DuiwbnU dnwuaibn duwnüduwnaDwA',
  //     ' fdujeanudinwa undwhd uwnb duwnudhnwudhnwu bndüuwAN DuiwbnU dnwuaibn duwnüduwnaDwA',
  //     ' fdujeanudinwa undwhd uwnb duwnudhnwudhnwu bndüuwAN DuiwbnU dnwuaibn duwnüduwnaDwA',
  //   ], generation: "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Lorem ipsum dolor sit amet, consectetur adipiscing elit.Lorem ipsum dolor sit amet, consectetur adipiscing elit.Lorem ipsum dolor sit amet, consectetur adipiscing elit.Lorem ipsum dolor sit amet, consectetur adipiscing elit.Lorem ipsum dolor sit amet, consectetur adipiscing elit."
  // }).pipe(
  //     delay(1000),
  //     tap(answers => {
  //       this.currentAnswersSubject.next(answers);
  //     })
  //   );

    let body: any = {
      question,
      language: 'en',
    };

    if (manufacturer) {
      body = {...body, manufacturer};
    }

    if (product) {
      body = {...body, product};
    }

    return this.http
      .post<any>('http://127.0.0.1:8000/getPredictedAnswers/', body)
      .pipe(
        tap(answers => {
          this.currentAnswersSubject.next(answers);
        }),
      );
  }

  invalidateAnswers() {
    this.currentAnswersSubject.next(null);
  }

  selectProductsForManufacturer(manufacturer: string) {
    return this.products$.pipe(
      map((products) => (products ? products[manufacturer] : []))
    );
  }
}
