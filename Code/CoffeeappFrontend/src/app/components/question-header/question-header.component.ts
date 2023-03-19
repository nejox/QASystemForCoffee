import {ChangeDetectionStrategy, Component, Input} from '@angular/core';

@Component({
  selector: 'app-question-header',
  templateUrl: './question-header.component.html',
  styleUrls: ['./question-header.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class QuestionHeaderComponent {
  @Input() question!: string;
}
