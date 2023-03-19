import {Component, OnInit} from '@angular/core';
import {FormControl, FormGroup, Validators} from '@angular/forms';
import {
  BehaviorSubject,
  catchError,
  combineLatest, distinctUntilChanged,
  EMPTY,
  filter,
  map,
  Observable,
  startWith,
  switchMap,
  tap
} from 'rxjs';
import {AnswerObject, CoffeeService} from './services/coffee.service';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss'],
})
export class AppComponent {
  coffeeForm!: FormGroup;

  answersAreLoading$!: Observable<boolean>;
  isSubmitButtonDisabled$!: Observable<boolean>;

  manufacturers$!: Observable<string[]>;
  products$!: Observable<string[]>;
  answerObject$!: Observable<AnswerObject | null>;

  private isLoadingSubject!: BehaviorSubject<boolean>;

  get manufacturerControl() {
    return this.coffeeForm.get('manufacturer');
  }

  get productControl() {
    return this.coffeeForm.get('product')
  }

  constructor(private coffeeService: CoffeeService) {
  }

  ngOnInit() {
    this.isLoadingSubject = new BehaviorSubject<boolean>(false);
    this.answersAreLoading$ = this.isLoadingSubject.asObservable();

    this.coffeeForm = new FormGroup({
      manufacturer: new FormControl(''),
      product: new FormControl({value: '', disabled: true}, ),
      question: new FormControl('', Validators.required),
    });

    this.isSubmitButtonDisabled$ = combineLatest([
      this.answersAreLoading$,
      this.coffeeForm.statusChanges.pipe(startWith('INVALID')),
    ]).pipe(
      map(([isLoading, coffeeFormStatus]) => isLoading === true || coffeeFormStatus === 'INVALID'),
      distinctUntilChanged(),
    );

    this.manufacturers$ = this.coffeeService.manufacturers$;

    this.answerObject$ = this.coffeeService.currentAnswers$;

    this.products$ = this.manufacturerControl!.valueChanges.pipe(
      tap(manufacturer => {
        this.productControl?.reset('');

        if (manufacturer) {
          this.productControl?.enable();
        } else {
          this.productControl?.disable();
        }
      }),
      switchMap((manufacturer) =>
        this.coffeeService.selectProductsForManufacturer(manufacturer)
      )
    );

    this.coffeeForm.valueChanges.pipe(
      tap(_ => this.coffeeService.invalidateAnswers()),
    ).subscribe();

    this.coffeeService.getProductsForAllManufacturer().subscribe();
  }

  sendQuestion() {
    if (this.coffeeForm.invalid) {
      return;
    }

    this.isLoadingSubject.next(true);
    this.coffeeService.getPredictedAnswers(this.coffeeForm.value).pipe(
      tap(_ => this.isLoadingSubject.next(false)),
      catchError(e => {
        this.isLoadingSubject.next(false);
        return EMPTY;
      }),
    ).subscribe();
  }
}
